#!/usr/bin/env python3
"""
CUDA-optimized thermal foliage segmentation for Jetson Orin Nano.
Real-time processing for 5-second thermal image capture intervals.
"""

import numpy as np
import cv2
import time
import logging
from typing import Tuple, Dict, Optional, List
from pathlib import Path

try:
    import cupy as cp
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False
    print("Warning: CuPy not available. Falling back to CPU processing.")

class CudaThermalFoliageSegmentor:
    """
    CUDA-accelerated thermal foliage segmentation for real-time processing.
    Optimized for Jetson Orin Nano with adjustable parameters.
    """
    
    def __init__(self, 
                 foliage_temp_range: Tuple[float, float] = (24.68, 25.55),
                 temp_tolerance: float = 0.3,
                 morphology_kernel_size: int = 3,
                 min_region_size: int = 50,
                 use_cuda: bool = True):
        """
        Initialize the CUDA thermal segmentor.
        
        Args:
            foliage_temp_range: Temperature range for foliage detection (°C)
            temp_tolerance: Temperature tolerance for region growing (°C)
            morphology_kernel_size: Size of morphological operations kernel
            min_region_size: Minimum size of valid foliage regions (pixels)
            use_cuda: Enable CUDA acceleration if available
        """
        self.foliage_temp_range = foliage_temp_range
        self.temp_tolerance = temp_tolerance
        self.morphology_kernel_size = morphology_kernel_size
        self.min_region_size = min_region_size
        self.use_cuda = use_cuda and CUDA_AVAILABLE
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize CUDA if available
        if self.use_cuda:
            try:
                cp.cuda.Device(0).use()
                self.logger.info("CUDA acceleration enabled on Jetson Orin Nano")
            except Exception as e:
                self.logger.warning(f"CUDA initialization failed: {e}. Using CPU.")
                self.use_cuda = False
        
        # Create morphological kernel
        self.kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, 
            (self.morphology_kernel_size, self.morphology_kernel_size)
        )
        
        # Performance metrics
        self.processing_times = []
        
    def process_thermal_image(self, thermal_image: np.ndarray) -> Dict:
        """
        Process thermal image to extract foliage temperature.
        Optimized for 5-second processing intervals.
        
        Args:
            thermal_image: Input thermal image array (H, W) in Celsius
            
        Returns:
            Dictionary with foliage temperature and segmentation metrics
        """
        start_time = time.time()
        
        try:
            # Convert to appropriate array type
            if self.use_cuda:
                thermal_gpu = cp.asarray(thermal_image, dtype=cp.float32)
                result = self._process_cuda(thermal_gpu)
            else:
                result = self._process_cpu(thermal_image.astype(np.float32))
            
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            result['processing_time'] = processing_time
            result['cuda_used'] = self.use_cuda
            
            self.logger.info(f"Processed thermal image in {processing_time:.3f}s (CUDA: {self.use_cuda})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing thermal image: {e}")
            return {
                'foliage_temperature': 0.0,
                'foliage_pixels': 0,
                'total_pixels': thermal_image.size,
                'segmentation_ratio': 0.0,
                'num_components': 0,
                'processing_time': time.time() - start_time,
                'cuda_used': self.use_cuda,
                'error': str(e)
            }
    
    def _process_cuda(self, thermal_gpu: 'cp.ndarray') -> Dict:
        """CUDA-accelerated processing pipeline."""
        # Step 1: Temperature thresholding
        min_temp, max_temp = self.foliage_temp_range
        temp_mask = (thermal_gpu >= min_temp) & (thermal_gpu <= max_temp)
        
        # Step 2: Morphological operations (using OpenCV on CPU for now)
        temp_mask_cpu = cp.asnumpy(temp_mask).astype(np.uint8) * 255
        
        # Opening (remove noise)
        opened = cv2.morphologyEx(temp_mask_cpu, cv2.MORPH_OPEN, self.kernel)
        
        # Closing (fill gaps)
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self.kernel)
        
        # Step 3: Connected components analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned)
        
        # Filter by minimum region size
        valid_components = []
        final_mask = np.zeros_like(cleaned)
        
        for i in range(1, num_labels):  # Skip background (label 0)
            if stats[i, cv2.CC_STAT_AREA] >= self.min_region_size:
                valid_components.append(i)
                final_mask[labels == i] = 255
        
        # Step 4: Calculate foliage temperature
        if len(valid_components) > 0:
            final_mask_gpu = cp.asarray(final_mask > 0)
            foliage_temps = thermal_gpu[final_mask_gpu]
            foliage_temperature = float(cp.mean(foliage_temps))
            foliage_pixels = int(cp.sum(final_mask_gpu))
        else:
            foliage_temperature = 0.0
            foliage_pixels = 0
        
        total_pixels = thermal_gpu.size
        segmentation_ratio = foliage_pixels / total_pixels
        
        return {
            'foliage_temperature': foliage_temperature,
            'foliage_pixels': foliage_pixels,
            'total_pixels': total_pixels,
            'segmentation_ratio': segmentation_ratio,
            'num_components': len(valid_components),
            'temperature_range': self.foliage_temp_range,
            'temp_tolerance': self.temp_tolerance
        }
    
    def _process_cpu(self, thermal_image: np.ndarray) -> Dict:
        """CPU-based processing pipeline."""
        # Step 1: Temperature thresholding
        min_temp, max_temp = self.foliage_temp_range
        temp_mask = (thermal_image >= min_temp) & (thermal_image <= max_temp)
        temp_mask = (temp_mask * 255).astype(np.uint8)
        
        # Step 2: Morphological operations
        opened = cv2.morphologyEx(temp_mask, cv2.MORPH_OPEN, self.kernel)
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, self.kernel)
        
        # Step 3: Connected components analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned)
        
        # Filter by minimum region size
        valid_components = []
        final_mask = np.zeros_like(cleaned)
        
        for i in range(1, num_labels):  # Skip background (label 0)
            if stats[i, cv2.CC_STAT_AREA] >= self.min_region_size:
                valid_components.append(i)
                final_mask[labels == i] = 255
        
        # Step 4: Calculate foliage temperature
        if len(valid_components) > 0:
            foliage_mask = final_mask > 0
            foliage_temps = thermal_image[foliage_mask]
            foliage_temperature = float(np.mean(foliage_temps))
            foliage_pixels = int(np.sum(foliage_mask))
        else:
            foliage_temperature = 0.0
            foliage_pixels = 0
        
        total_pixels = thermal_image.size
        segmentation_ratio = foliage_pixels / total_pixels
        
        return {
            'foliage_temperature': foliage_temperature,
            'foliage_pixels': foliage_pixels,
            'total_pixels': total_pixels,
            'segmentation_ratio': segmentation_ratio,
            'num_components': len(valid_components),
            'temperature_range': self.foliage_temp_range,
            'temp_tolerance': self.temp_tolerance
        }
    
    def update_parameters(self, **kwargs):
        """
        Update segmentation parameters dynamically.
        
        Args:
            foliage_temp_range: New temperature range tuple
            temp_tolerance: New temperature tolerance
            morphology_kernel_size: New kernel size
            min_region_size: New minimum region size
        """
        if 'foliage_temp_range' in kwargs:
            self.foliage_temp_range = kwargs['foliage_temp_range']
            
        if 'temp_tolerance' in kwargs:
            self.temp_tolerance = kwargs['temp_tolerance']
            
        if 'morphology_kernel_size' in kwargs:
            self.morphology_kernel_size = kwargs['morphology_kernel_size']
            self.kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, 
                (self.morphology_kernel_size, self.morphology_kernel_size)
            )
            
        if 'min_region_size' in kwargs:
            self.min_region_size = kwargs['min_region_size']
        
        self.logger.info(f"Updated parameters: {kwargs}")
    
    def get_performance_stats(self) -> Dict:
        """Get processing performance statistics."""
        if not self.processing_times:
            return {'avg_time': 0.0, 'max_time': 0.0, 'min_time': 0.0, 'count': 0}
        
        return {
            'avg_time': np.mean(self.processing_times),
            'max_time': np.max(self.processing_times),
            'min_time': np.min(self.processing_times),
            'count': len(self.processing_times),
            'cuda_available': CUDA_AVAILABLE,
            'cuda_used': self.use_cuda
        }
    
    def get_current_parameters(self) -> Dict:
        """Get current segmentation parameters."""
        return {
            'foliage_temp_range': self.foliage_temp_range,
            'temp_tolerance': self.temp_tolerance,
            'morphology_kernel_size': self.morphology_kernel_size,
            'min_region_size': self.min_region_size,
            'use_cuda': self.use_cuda,
            'cuda_available': CUDA_AVAILABLE
        }


def test_segmentor():
    """Test the segmentor with synthetic data."""
    print("🌿 Testing CUDA Thermal Foliage Segmentor")
    print("=" * 50)
    
    # Create synthetic thermal image
    thermal_image = np.random.normal(25.0, 0.8, (120, 160))
    
    # Add foliage regions
    foliage_centers = [(40, 60), (80, 100)]
    for center_y, center_x in foliage_centers:
        y, x = np.ogrid[:120, :160]
        mask = (y - center_y)**2 + (x - center_x)**2 <= 400
        thermal_image[mask] = np.random.uniform(24.8, 25.2, np.sum(mask))
    
    # Initialize segmentor
    segmentor = CudaThermalFoliageSegmentor()
    
    # Process image
    result = segmentor.process_thermal_image(thermal_image)
    
    print(f"Foliage Temperature: {result['foliage_temperature']:.2f}°C")
    print(f"Segmentation Ratio: {result['segmentation_ratio']:.3f}")
    print(f"Processing Time: {result['processing_time']:.3f}s")
    print(f"CUDA Used: {result['cuda_used']}")
    
    return segmentor


if __name__ == "__main__":
    test_segmentor()
