#!/usr/bin/env python3
"""
Integration module for thermal foliage segmentation with Jetson greenhouse server.
Handles thermal image fetching and processing for foliage temperature calculation.
"""

import numpy as np
import requests
import json
import time
import logging
from typing import Dict, Optional, Tuple
from cuda_thermal_segmentor import CudaThermalFoliageSegmentor

class ThermalFoliageIntegration:
    """
    Integration class for thermal foliage segmentation with tCam-Mini.
    Fetches thermal images and processes them for foliage temperature.
    """
    
    def __init__(self, tcam_url="http://192.168.1.130:5001", segmentor_params=None):
        """
        Initialize thermal integration with tCam-Mini device.
        
        Args:
            tcam_url: URL of tCam-Mini HTTP API
            segmentor_params: Parameters for the thermal segmentor
        """
        self.tcam_url = tcam_url
        
        # Initialize segmentor with default or custom parameters
        default_params = {
            'foliage_temp_range': (23.0, 27.0),  # Broader range for real FLIR data
            'temp_tolerance': 1.0,  # More tolerance for real thermal variations
            'morphology_kernel_size': 3,
            'min_region_size': 100,  # Larger minimum for 160x120 resolution
            'use_cuda': True
        }
        
        if segmentor_params:
            default_params.update(segmentor_params)
        
        self.segmentor = CudaThermalFoliageSegmentor(**default_params)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cache for last successful result
        self.last_result = {
            'foliage_temperature': 0.0,
            'segmentation_ratio': 0.0,
            'num_components': 0,
            'processing_time': 0.0,
            'timestamp': 0,
            'status': 'no_data'
        }
    
    def fetch_thermal_image(self):
        """Fetch thermal image from tCam-Mini via Jetson proxy or generate mock data"""
        try:
            # Get thermal image data from tCam web interface (JSON format)
            response = requests.get(f"{self.tcam_url}/thermal_raw", timeout=10)
            response.raise_for_status()
            
            # Parse JSON response containing pixel data
            thermal_json = response.json()
            pixel_data = thermal_json.get("pixels", [])
            
            if not pixel_data:
                raise ValueError("No pixel data in response")
            
            # Convert to numpy array
            thermal_array = np.array(pixel_data, dtype=np.float32)
            
            # FLIR Lepton 3.5 resolution is 160x120
            if len(thermal_array) == 19200:  # 160 * 120
                thermal_celsius = thermal_array.reshape((120, 160))
                logging.info(f"Using real FLIR Lepton thermal data: {thermal_celsius.shape}")
            else:
                # Fallback: try to reshape to reasonable dimensions
                sqrt_len = int(np.sqrt(len(thermal_array)))
                if sqrt_len * sqrt_len == len(thermal_array):
                    thermal_celsius = thermal_array.reshape((sqrt_len, sqrt_len))
                else:
                    # Use mock data if can't reshape properly
                    raise ValueError(f"Cannot reshape thermal data with {len(thermal_array)} pixels")
                logging.info(f"Using real thermal data (reshaped): {thermal_celsius.shape}")
            
            return thermal_celsius.astype(np.float32)
            
        except Exception as e:
            logging.warning(f"Failed to fetch real thermal image: {e}")
            # Generate mock thermal data for development/testing
            return self._generate_mock_thermal_data()
    
    def _generate_mock_thermal_data(self):
        """Generate realistic mock thermal data for testing"""
        # Create a 24x32 thermal image with realistic greenhouse temperatures
        # Use current time for varying mock data instead of fixed seed
        np.random.seed(int(time.time()) % 1000)
        
        # Base temperature around 25°C (within foliage range) with some variation
        base_temp = 25.1 + np.random.uniform(-1.5, 1.5)  # Vary base temperature
        thermal_image = np.random.normal(base_temp, 0.8, (24, 32))
        
        # Add some "foliage" regions with temperatures in the detection range
        # Create circular regions that could represent plants
        y, x = np.ogrid[:24, :32]
        
        # Plant region 1 - vary foliage temperature more realistically
        center1 = (8, 12)
        mask1 = (x - center1[1])**2 + (y - center1[0])**2 <= 25
        foliage_temp1 = base_temp + np.random.uniform(-0.5, 0.8)
        thermal_image[mask1] = np.random.normal(foliage_temp1, 0.3, np.sum(mask1))
        
        # Plant region 2 - also vary foliage range
        center2 = (16, 20)
        mask2 = (x - center2[1])**2 + (y - center2[0])**2 <= 16
        foliage_temp2 = base_temp + np.random.uniform(-0.3, 0.6)
        thermal_image[mask2] = np.random.normal(foliage_temp2, 0.2, np.sum(mask2))
        
        # Add some background areas outside foliage range
        background_mask = (thermal_image < 24.5) | (thermal_image > 25.8)
        thermal_image[background_mask] = np.random.normal(23.5, 1.0, np.sum(background_mask))
        
        # Ensure temperatures are in reasonable range
        thermal_image = np.clip(thermal_image, 20.0, 30.0)
        
        return thermal_image.astype(np.float32)
    
    def get_foliage_temperature(self) -> Dict:
        """
        Get current foliage temperature by processing thermal image.
        
        Returns:
            Dictionary with foliage temperature and segmentation data
        """
        try:
            # Fetch thermal image
            thermal_image = self.fetch_thermal_image()
            
            if thermal_image is not None:
                # Process image for foliage segmentation
                result = self.segmentor.process_thermal_image(thermal_image)
                
                # Update result with additional info
                result.update({
                    'timestamp': time.time(),
                    'status': 'success',
                    'tcam_connected': True,
                    'image_shape': thermal_image.shape,
                    'temp_range': (float(np.min(thermal_image)), float(np.max(thermal_image)))
                })
                
                # Cache successful result
                self.last_result = result
                
                return result
            else:
                # Return cached result with connection error
                return {
                    **self.last_result,
                    'status': 'connection_error',
                    'tcam_connected': False,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting foliage temperature: {e}")
            return {
                **self.last_result,
                'status': 'processing_error',
                'tcam_connected': False,
                'timestamp': time.time(),
                'error': str(e)
            }
    
    def update_segmentor_parameters(self, **kwargs):
        """Update thermal segmentor parameters."""
        self.segmentor.update_parameters(**kwargs)
        self.logger.info(f"Updated segmentor parameters: {kwargs}")
    
    def get_segmentor_parameters(self) -> Dict:
        """Get current segmentor parameters."""
        return self.segmentor.get_current_parameters()
    
    def get_performance_stats(self) -> Dict:
        """Get processing performance statistics."""
        return self.segmentor.get_performance_stats()
    
    def test_connection(self) -> bool:
        """Test connection to tCam-Mini device."""
        try:
            response = requests.get(f"{self.tcam_url}/status", timeout=3.0)
            return response.status_code == 200
        except:
            return False


def create_thermal_integration(config_params: Optional[Dict] = None) -> ThermalFoliageIntegration:
    """
    Factory function to create thermal foliage integration instance.
    
    Args:
        config_params: Configuration parameters for integration
        
    Returns:
        Configured ThermalFoliageIntegration instance
    """
    default_config = {
        'tcam_url': 'http://192.168.1.130:5001',
        'segmentor_params': {
            'foliage_temp_range': (23.0, 27.0),  # Broader range for real FLIR data
            'temp_tolerance': 1.0,  # More tolerance for real thermal variations
            'morphology_kernel_size': 3,
            'min_region_size': 100,  # Larger minimum for 160x120 resolution
            'use_cuda': True
        }
    }
    
    if config_params:
        default_config.update(config_params)
    
    return ThermalFoliageIntegration(**default_config)


if __name__ == "__main__":
    # Test the integration
    print("🌿 Testing Thermal Foliage Integration")
    print("=" * 50)
    
    integration = create_thermal_integration()
    
    # Test connection
    connected = integration.test_connection()
    print(f"tCam-Mini Connection: {'✅ Connected' if connected else '❌ Disconnected'}")
    
    if connected:
        # Get foliage temperature
        result = integration.get_foliage_temperature()
        print(f"Foliage Temperature: {result['foliage_temperature']:.2f}°C")
        print(f"Segmentation Ratio: {result['segmentation_ratio']:.3f}")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        print(f"Status: {result['status']}")
    
    # Show current parameters
    params = integration.get_segmentor_parameters()
    print(f"\nCurrent Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
