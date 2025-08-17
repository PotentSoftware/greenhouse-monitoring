#!/usr/bin/env python3
"""
Thermal Image Collector for Jetson Orin Nano
Collects series of thermal images for statistical analysis and processing experiments
"""

import os
import time
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from sensor_manager import SensorManager
import json

class ThermalImageCollector:
    """Collects thermal images for analysis and processing experiments"""
    
    def __init__(self, config, sensor_manager: SensorManager):
        self.config = config
        self.sensor_manager = sensor_manager
        self.desktop_path = Path.home() / "Desktop"
        
        # Ensure Desktop directory exists
        self.desktop_path.mkdir(exist_ok=True)
        
        logging.info("🖼️ Thermal Image Collector initialized")
    
    def create_timestamped_directory(self) -> Path:
        """Create a timestamped directory for image collection"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        collection_dir = self.desktop_path / f"thermal_collection_{timestamp}"
        collection_dir.mkdir(exist_ok=True)
        
        logging.info(f"📁 Created collection directory: {collection_dir}")
        return collection_dir
    
    def capture_single_thermal_image(self) -> Optional[np.ndarray]:
        """Capture a single thermal image and return as numpy array"""
        try:
            # Update thermal camera data
            success = self.sensor_manager.fetch_thermal_data()
            if not success:
                logging.warning("⚠️ Failed to fetch thermal data")
                return None
            
            # Get the raw thermal image
            sensor_data = self.sensor_manager.get_sensor_data()
            thermal_data = sensor_data.get("thermal_camera", {})
            raw_image = thermal_data.get("raw_image")
            
            if raw_image is None:
                logging.warning("⚠️ No raw thermal image available")
                return None
            
            return raw_image.copy()
            
        except Exception as e:
            logging.error(f"❌ Error capturing thermal image: {e}")
            return None
    
    def collect_image_series(self, num_images: int = 10, interval_seconds: int = 5) -> Dict[str, Any]:
        """
        Collect a series of thermal images
        
        Args:
            num_images: Number of images to collect (default: 10)
            interval_seconds: Seconds between captures (default: 5)
            
        Returns:
            Dictionary with collection results and metadata
        """
        collection_dir = self.create_timestamped_directory()
        
        # Collection metadata
        metadata = {
            "collection_start": datetime.now().isoformat(),
            "num_images_requested": num_images,
            "interval_seconds": interval_seconds,
            "collection_directory": str(collection_dir),
            "images_captured": [],
            "capture_errors": [],
            "thermal_camera_config": {
                "host": self.config.TCAM_HOST,
                "port": self.config.TCAM_PORT,
                "resolution": f"{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}",
                "thermal_resolution": self.config.THERMAL_RESOLUTION,
                "kelvin_offset": self.config.KELVIN_OFFSET
            }
        }
        
        logging.info(f"🎯 Starting thermal image collection: {num_images} images, {interval_seconds}s intervals")
        
        captured_images = []
        
        for i in range(num_images):
            logging.info(f"📸 Capturing image {i+1}/{num_images}...")
            
            # Capture thermal image
            thermal_image = self.capture_single_thermal_image()
            
            if thermal_image is not None:
                # Generate filename with timestamp and sequence number
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
                filename = f"thermal_image_{i+1:02d}_{timestamp}.npy"
                filepath = collection_dir / filename
                
                try:
                    # Save as .npy file
                    np.save(filepath, thermal_image)
                    
                    # Calculate basic statistics for metadata
                    valid_pixels = thermal_image[thermal_image >= 0]
                    image_stats = {
                        "filename": filename,
                        "capture_time": datetime.now().isoformat(),
                        "sequence_number": i + 1,
                        "image_shape": thermal_image.shape,
                        "min_temp": float(np.min(valid_pixels)) if len(valid_pixels) > 0 else None,
                        "max_temp": float(np.max(valid_pixels)) if len(valid_pixels) > 0 else None,
                        "mean_temp": float(np.mean(valid_pixels)) if len(valid_pixels) > 0 else None,
                        "total_pixels": thermal_image.size,
                        "valid_pixels": len(valid_pixels),
                        "negative_pixels": thermal_image.size - len(valid_pixels)
                    }
                    
                    metadata["images_captured"].append(image_stats)
                    captured_images.append(thermal_image)
                    
                    logging.info(f"✅ Saved {filename} - Temp range: {image_stats['min_temp']:.1f}°C to {image_stats['max_temp']:.1f}°C")
                    
                except Exception as e:
                    error_msg = f"Failed to save image {i+1}: {e}"
                    logging.error(f"❌ {error_msg}")
                    metadata["capture_errors"].append({
                        "sequence_number": i + 1,
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                error_msg = f"Failed to capture image {i+1}"
                logging.error(f"❌ {error_msg}")
                metadata["capture_errors"].append({
                    "sequence_number": i + 1,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait for next capture (except for last image)
            if i < num_images - 1:
                logging.info(f"⏱️ Waiting {interval_seconds} seconds for next capture...")
                time.sleep(interval_seconds)
        
        # Finalize metadata
        metadata["collection_end"] = datetime.now().isoformat()
        metadata["images_successfully_captured"] = len(metadata["images_captured"])
        metadata["total_errors"] = len(metadata["capture_errors"])
        
        # Save metadata as JSON
        metadata_file = collection_dir / "collection_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logging.info(f"📋 Saved collection metadata: {metadata_file}")
        except Exception as e:
            logging.error(f"❌ Failed to save metadata: {e}")
        
        # Create summary file
        summary_file = collection_dir / "README.txt"
        try:
            with open(summary_file, 'w') as f:
                f.write(f"Thermal Image Collection Summary\n")
                f.write(f"================================\n\n")
                f.write(f"Collection Date: {metadata['collection_start']}\n")
                f.write(f"Images Requested: {metadata['num_images_requested']}\n")
                f.write(f"Images Captured: {metadata['images_successfully_captured']}\n")
                f.write(f"Capture Interval: {metadata['interval_seconds']} seconds\n")
                f.write(f"Total Errors: {metadata['total_errors']}\n\n")
                f.write(f"Files in this directory:\n")
                f.write(f"- thermal_image_XX_YYYYMMDD_HHMMSS_mmm.npy: Raw thermal data arrays\n")
                f.write(f"- collection_metadata.json: Detailed collection metadata\n")
                f.write(f"- README.txt: This summary file\n\n")
                f.write(f"Image Format:\n")
                f.write(f"- NumPy arrays in .npy format\n")
                f.write(f"- Shape: {self.config.IMAGE_HEIGHT}x{self.config.IMAGE_WIDTH} pixels\n")
                f.write(f"- Data type: float64 (temperature in Celsius)\n")
                f.write(f"- Negative values indicate faulty pixels\n\n")
                f.write(f"Usage:\n")
                f.write(f"import numpy as np\n")
                f.write(f"thermal_data = np.load('thermal_image_01_YYYYMMDD_HHMMSS_mmm.npy')\n")
            
            logging.info(f"📄 Created summary file: {summary_file}")
        except Exception as e:
            logging.error(f"❌ Failed to create summary file: {e}")
        
        logging.info(f"🎉 Collection complete! {metadata['images_successfully_captured']}/{num_images} images saved to {collection_dir}")
        
        return {
            "success": metadata['images_successfully_captured'] > 0,
            "collection_directory": str(collection_dir),
            "images_captured": metadata['images_successfully_captured'],
            "total_requested": num_images,
            "errors": metadata['total_errors'],
            "metadata": metadata,
            "thermal_arrays": captured_images
        }
    
    def get_collection_status(self) -> Dict[str, Any]:
        """Get status of thermal image collection capability"""
        # Test thermal camera connection
        test_image = self.capture_single_thermal_image()
        
        return {
            "thermal_camera_connected": test_image is not None,
            "desktop_path": str(self.desktop_path),
            "desktop_writable": os.access(self.desktop_path, os.W_OK),
            "config": {
                "tcam_host": self.config.TCAM_HOST,
                "tcam_port": self.config.TCAM_PORT,
                "image_dimensions": f"{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}",
                "thermal_resolution": self.config.THERMAL_RESOLUTION
            }
        }
