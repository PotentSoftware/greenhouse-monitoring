#!/usr/bin/env python3
"""
Thermal Image Processor for Jetson Orin Nano
Handles thermal image processing with pluggable strategies for future OpenCV integration
"""

import numpy as np
import cv2
import logging
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib.colors import LinearSegmentedColormap
import io
import base64
from typing import Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod

class ThermalProcessorStrategy(ABC):
    """Abstract base class for thermal processing strategies"""
    
    @abstractmethod
    def process_image(self, thermal_image: np.ndarray) -> Dict[str, Any]:
        """Process thermal image and return analysis results"""
        pass
    
    @abstractmethod
    def get_canopy_temperature(self, thermal_image: np.ndarray) -> float:
        """Extract canopy temperature from thermal image"""
        pass

class BasicThermalProcessor(ThermalProcessorStrategy):
    """Basic thermal processing using statistical analysis"""
    
    def process_image(self, thermal_image: np.ndarray) -> Dict[str, Any]:
        """Process thermal image using basic statistical methods"""
        if thermal_image is None or thermal_image.size == 0:
            return {}
        
        # Filter out negative values (faulty pixels)
        valid_pixels = thermal_image[thermal_image >= 0]
        
        if len(valid_pixels) == 0:
            return {}
        
        results = {
            'min_temp': float(np.min(valid_pixels)),
            'max_temp': float(np.max(valid_pixels)),
            'mean_temp': float(np.mean(valid_pixels)),
            'median_temp': float(np.median(valid_pixels)),
            'std_temp': float(np.std(valid_pixels)),
            'total_pixels': thermal_image.size,
            'valid_pixels': len(valid_pixels),
            'processing_method': 'basic_statistical'
        }
        
        # Calculate mode (most frequent temperature)
        rounded_pixels = np.round(valid_pixels * 10) / 10
        unique_temps, counts = np.unique(rounded_pixels, return_counts=True)
        results['mode_temp'] = float(unique_temps[np.argmax(counts)])
        
        return results
    
    def get_canopy_temperature(self, thermal_image: np.ndarray) -> float:
        """Get canopy temperature using current BeaglePlay method (average)"""
        if thermal_image is None or thermal_image.size == 0:
            return None
        
        valid_pixels = thermal_image[thermal_image >= 0]
        if len(valid_pixels) == 0:
            return None
        
        return float(np.mean(valid_pixels))

class OpenCVSimpleProcessor(ThermalProcessorStrategy):
    """Simple OpenCV-based thermal processing"""
    
    def __init__(self):
        self.threshold_multiplier = 1.5
        self.kernel_size = 3
        self.min_area = 50
        self.max_area = 2000
    
    def process_image(self, thermal_image: np.ndarray) -> Dict[str, Any]:
        """Process thermal image using simple OpenCV methods"""
        if thermal_image is None or thermal_image.size == 0:
            return {}
        
        # Basic statistical analysis first
        basic_processor = BasicThermalProcessor()
        results = basic_processor.process_image(thermal_image)
        
        try:
            # Convert to 8-bit for OpenCV processing
            thermal_norm = cv2.normalize(thermal_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(thermal_norm, (5, 5), 0)
            
            # Threshold to find hot regions
            mean_temp = results.get('mean_temp', 0)
            threshold_temp = mean_temp * self.threshold_multiplier
            
            # Convert threshold back to 8-bit scale
            threshold_8bit = int((threshold_temp - thermal_image.min()) / (thermal_image.max() - thermal_image.min()) * 255)
            threshold_8bit = max(0, min(255, threshold_8bit))
            
            _, thresh = cv2.threshold(blurred, threshold_8bit, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to clean up regions
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.kernel_size, self.kernel_size))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
            
            # Find contours (regions)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if self.min_area <= area <= self.max_area:
                    valid_contours.append(contour)
            
            results.update({
                'processing_method': 'opencv_simple',
                'regions_detected': len(valid_contours),
                'threshold_temperature': threshold_temp,
                'opencv_params': {
                    'threshold_multiplier': self.threshold_multiplier,
                    'kernel_size': self.kernel_size,
                    'min_area': self.min_area,
                    'max_area': self.max_area
                }
            })
            
        except Exception as e:
            logging.warning(f"⚠️ OpenCV processing failed, using basic method: {e}")
            results['processing_method'] = 'basic_fallback'
        
        return results
    
    def get_canopy_temperature(self, thermal_image: np.ndarray) -> float:
        """Get canopy temperature using OpenCV region analysis"""
        # For now, fall back to basic method
        # Future enhancement: use detected regions for more accurate canopy temp
        basic_processor = BasicThermalProcessor()
        return basic_processor.get_canopy_temperature(thermal_image)

class ThermalProcessor:
    """Main thermal processor with pluggable strategies"""
    
    def __init__(self, config):
        self.config = config
        self.current_strategy = 'basic'
        self.strategies = {
            'basic': BasicThermalProcessor(),
            'opencv_simple': OpenCVSimpleProcessor()
        }
        
        # Create thermal colormap for visualization
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        self.thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
        
        logging.info(f"🖼️ Thermal Processor initialized with strategy: {self.current_strategy}")
    
    def set_processing_strategy(self, strategy_name: str) -> bool:
        """Set the thermal processing strategy"""
        if strategy_name in self.strategies:
            self.current_strategy = strategy_name
            logging.info(f"🔄 Thermal processing strategy changed to: {strategy_name}")
            return True
        else:
            logging.warning(f"⚠️ Unknown thermal processing strategy: {strategy_name}")
            return False
    
    def process_thermal_image(self, thermal_image: np.ndarray) -> Dict[str, Any]:
        """Process thermal image using current strategy"""
        if thermal_image is None:
            return {}
        
        try:
            strategy = self.strategies[self.current_strategy]
            results = strategy.process_image(thermal_image)
            results['strategy_used'] = self.current_strategy
            return results
        except Exception as e:
            logging.error(f"❌ Thermal processing error: {e}")
            return {}
    
    def get_canopy_temperature(self, thermal_image: np.ndarray) -> float:
        """Get canopy temperature using current strategy"""
        if thermal_image is None:
            return None
        
        try:
            strategy = self.strategies[self.current_strategy]
            return strategy.get_canopy_temperature(thermal_image)
        except Exception as e:
            logging.error(f"❌ Canopy temperature calculation error: {e}")
            return None
    
    def generate_thermal_visualization(self, thermal_image: np.ndarray) -> str:
        """Generate thermal image visualization as base64 string"""
        if thermal_image is None or thermal_image.size == 0:
            return None
        
        try:
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Display thermal image with colormap
            im = ax.imshow(thermal_image, cmap=self.thermal_cmap, aspect='auto')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Temperature (°C)', rotation=270, labelpad=20)
            
            # Set title and labels
            ax.set_title('Thermal Image', fontsize=14, fontweight='bold')
            ax.set_xlabel('Pixel X')
            ax.set_ylabel('Pixel Y')
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close(fig)
            
            return image_base64
            
        except Exception as e:
            logging.error(f"❌ Thermal visualization error: {e}")
            return None
    
    def get_available_strategies(self) -> Dict[str, str]:
        """Get available processing strategies"""
        return {
            'basic': 'Basic Statistical Analysis',
            'opencv_simple': 'Simple OpenCV Processing'
        }
    
    def add_strategy(self, name: str, strategy: ThermalProcessorStrategy):
        """Add a new processing strategy"""
        self.strategies[name] = strategy
        logging.info(f"➕ Added thermal processing strategy: {name}")
    
    def get_processing_info(self) -> Dict[str, Any]:
        """Get information about current processing setup"""
        return {
            'current_strategy': self.current_strategy,
            'available_strategies': list(self.strategies.keys()),
            'strategy_descriptions': self.get_available_strategies(),
            'image_dimensions': f"{self.config.IMAGE_WIDTH}x{self.config.IMAGE_HEIGHT}"
        }
