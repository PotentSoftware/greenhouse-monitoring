#!/usr/bin/env python3
"""
Leaf Detection Prototype for tCam-Mini Thermal Images

This script implements the basic computer vision pipeline for identifying
individual leaves in thermal images and calculating per-leaf temperature statistics.

This is a prototype to test the algorithms before full integration.
"""

import cv2
import numpy as np
import json
import matplotlib.pyplot as plt
from scipy import ndimage
from sklearn.cluster import DBSCAN
import os
from datetime import datetime

class LeafDetector:
    def __init__(self):
        # Tunable parameters for leaf detection
        self.params = {
            # Temperature thresholding
            'temp_threshold_offset': 2.0,  # Degrees above background
            'min_leaf_temp': 15.0,         # Minimum realistic leaf temperature
            'max_leaf_temp': 45.0,         # Maximum realistic leaf temperature
            
            # Morphological operations
            'morph_kernel_size': 3,
            'opening_iterations': 2,
            'closing_iterations': 3,
            
            # Size filtering
            'min_leaf_area': 50,           # Minimum pixels for a leaf
            'max_leaf_area': 2000,        # Maximum pixels for a leaf
            
            # Shape filtering
            'min_aspect_ratio': 0.3,      # Width/height ratio
            'max_aspect_ratio': 3.0,
            'min_solidity': 0.4,          # Area/convex_hull_area
            
            # Clustering for nearby regions
            'cluster_eps': 10,             # DBSCAN epsilon
            'cluster_min_samples': 2       # DBSCAN min samples
        }
        
        print("🌿 Leaf Detector initialized")
        print(f"📋 Parameters: {json.dumps(self.params, indent=2)}")
    
    def detect_leaves(self, thermal_image, temperature_array):
        """
        Main leaf detection pipeline
        
        Args:
            thermal_image: 2D numpy array representing thermal image
            temperature_array: 2D numpy array with temperature values
            
        Returns:
            dict with detected leaves and analysis results
        """
        print("🔍 Starting leaf detection pipeline...")
        
        # Step 1: Temperature-based thresholding
        leaf_mask = self._temperature_threshold(temperature_array)
        
        # Step 2: Morphological operations
        cleaned_mask = self._morphological_cleaning(leaf_mask)
        
        # Step 3: Connected component analysis
        labeled_regions = self._find_connected_components(cleaned_mask)
        
        # Step 4: Filter regions by size and shape
        valid_leaves = self._filter_leaf_regions(labeled_regions, temperature_array)
        
        # Step 5: Calculate statistics for each leaf
        leaf_analysis = self._analyze_leaves(valid_leaves, temperature_array)
        
        # Step 6: Population-level statistics
        population_stats = self._calculate_population_statistics(leaf_analysis)
        
        return {
            'detection_info': {
                'timestamp': datetime.now().isoformat(),
                'image_shape': thermal_image.shape,
                'total_pixels': thermal_image.size,
                'parameters_used': self.params
            },
            'processing_steps': {
                'initial_mask_pixels': np.sum(leaf_mask),
                'cleaned_mask_pixels': np.sum(cleaned_mask),
                'connected_components': len(np.unique(labeled_regions)) - 1,
                'valid_leaves_found': len(valid_leaves)
            },
            'leaf_analysis': leaf_analysis,
            'population_statistics': population_stats,
            'debug_images': {
                'original': thermal_image,
                'temperature_array': temperature_array,
                'initial_mask': leaf_mask,
                'cleaned_mask': cleaned_mask,
                'labeled_regions': labeled_regions
            }
        }
    
    def _temperature_threshold(self, temperature_array):
        """Create binary mask based on temperature thresholding"""
        print("🌡️ Applying temperature thresholding...")
        
        # Calculate background temperature (assume it's the mode or lower percentile)
        background_temp = np.percentile(temperature_array, 25)
        threshold_temp = background_temp + self.params['temp_threshold_offset']
        
        print(f"   Background temp: {background_temp:.2f}°C")
        print(f"   Threshold temp: {threshold_temp:.2f}°C")
        
        # Create mask for potential leaf pixels
        mask = (temperature_array > threshold_temp) & \
               (temperature_array >= self.params['min_leaf_temp']) & \
               (temperature_array <= self.params['max_leaf_temp'])
        
        print(f"   Pixels above threshold: {np.sum(mask)} / {mask.size}")
        return mask.astype(np.uint8)
    
    def _morphological_cleaning(self, binary_mask):
        """Clean binary mask using morphological operations"""
        print("🧹 Cleaning mask with morphological operations...")
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                         (self.params['morph_kernel_size'], 
                                          self.params['morph_kernel_size']))
        
        # Opening to remove noise
        opened = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, 
                                iterations=self.params['opening_iterations'])
        
        # Closing to fill gaps
        cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel,
                                 iterations=self.params['closing_iterations'])
        
        print(f"   Pixels after cleaning: {np.sum(cleaned)} (was {np.sum(binary_mask)})")
        return cleaned
    
    def _find_connected_components(self, binary_mask):
        """Find connected components in binary mask"""
        print("🔗 Finding connected components...")
        
        num_labels, labeled = cv2.connectedComponents(binary_mask)
        
        print(f"   Found {num_labels - 1} connected components")
        return labeled
    
    def _filter_leaf_regions(self, labeled_regions, temperature_array):
        """Filter regions by size and shape to identify valid leaves"""
        print("🍃 Filtering regions to identify valid leaves...")
        
        valid_leaves = []
        num_labels = len(np.unique(labeled_regions)) - 1
        
        for label in range(1, num_labels + 1):
            region_mask = (labeled_regions == label)
            
            # Size filtering
            area = np.sum(region_mask)
            if area < self.params['min_leaf_area'] or area > self.params['max_leaf_area']:
                continue
            
            # Shape analysis
            if not self._validate_leaf_shape(region_mask):
                continue
            
            valid_leaves.append({
                'label': label,
                'mask': region_mask,
                'area': area
            })
        
        print(f"   Valid leaves after filtering: {len(valid_leaves)}")
        return valid_leaves
    
    def _validate_leaf_shape(self, region_mask):
        """Validate if region has leaf-like shape characteristics"""
        # Find contours
        contours, _ = cv2.findContours(region_mask.astype(np.uint8), 
                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return False
        
        # Use largest contour
        contour = max(contours, key=cv2.contourArea)
        
        # Calculate shape metrics
        area = cv2.contourArea(contour)
        if area == 0:
            return False
        
        # Bounding rectangle for aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / h if h > 0 else 0
        
        # Convex hull for solidity
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Check shape criteria
        aspect_ok = (self.params['min_aspect_ratio'] <= aspect_ratio <= 
                    self.params['max_aspect_ratio'])
        solidity_ok = solidity >= self.params['min_solidity']
        
        return aspect_ok and solidity_ok
    
    def _analyze_leaves(self, valid_leaves, temperature_array):
        """Calculate detailed statistics for each detected leaf"""
        print("📊 Calculating per-leaf temperature statistics...")
        
        leaf_analysis = {
            'individual_leaves': [],
            'total_leaves_detected': len(valid_leaves)
        }
        
        for i, leaf in enumerate(valid_leaves):
            mask = leaf['mask']
            leaf_temps = temperature_array[mask]
            
            # Calculate centroid
            y_coords, x_coords = np.where(mask)
            centroid = [float(np.mean(x_coords)), float(np.mean(y_coords))]
            
            # Calculate bounding box
            min_x, max_x = np.min(x_coords), np.max(x_coords)
            min_y, max_y = np.min(y_coords), np.max(y_coords)
            bounding_box = [int(min_x), int(min_y), int(max_x), int(max_y)]
            
            # Temperature statistics
            leaf_stats = {
                'leaf_id': i + 1,
                'pixel_count': len(leaf_temps),
                'area_pixels': leaf['area'],
                'centroid': centroid,
                'bounding_box': bounding_box,
                'min_temp': float(np.min(leaf_temps)),
                'max_temp': float(np.max(leaf_temps)),
                'mean_temp': float(np.mean(leaf_temps)),
                'median_temp': float(np.median(leaf_temps)),
                'std_dev_temp': float(np.std(leaf_temps))
            }
            
            # Calculate mode (most frequent temperature, rounded to 0.1°C)
            rounded_temps = np.round(leaf_temps, 1)
            unique_temps, counts = np.unique(rounded_temps, return_counts=True)
            mode_temp = unique_temps[np.argmax(counts)]
            leaf_stats['mode_temp'] = float(mode_temp)
            
            leaf_analysis['individual_leaves'].append(leaf_stats)
        
        return leaf_analysis
    
    def _calculate_population_statistics(self, leaf_analysis):
        """Calculate statistics across all detected leaves"""
        print("🌱 Calculating population-level statistics...")
        
        if not leaf_analysis['individual_leaves']:
            return {
                'total_leaves': 0,
                'total_measurements': 0,
                'overall_min_temp': None,
                'overall_max_temp': None,
                'overall_mean_temp': None,
                'overall_median_temp': None,
                'overall_mode_temp': None,
                'overall_std_dev_temp': None
            }
        
        # Collect all temperature measurements
        all_temps = []
        for leaf in leaf_analysis['individual_leaves']:
            # We don't have individual pixel temps here, so use leaf means
            # In full implementation, we'd collect all pixel temperatures
            all_temps.append(leaf['mean_temp'])
        
        all_temps = np.array(all_temps)
        
        # Calculate mode of leaf mean temperatures
        rounded_temps = np.round(all_temps, 1)
        unique_temps, counts = np.unique(rounded_temps, return_counts=True)
        mode_temp = unique_temps[np.argmax(counts)]
        
        return {
            'total_leaves': len(leaf_analysis['individual_leaves']),
            'total_measurements': len(all_temps),
            'overall_min_temp': float(np.min(all_temps)),
            'overall_max_temp': float(np.max(all_temps)),
            'overall_mean_temp': float(np.mean(all_temps)),
            'overall_median_temp': float(np.median(all_temps)),
            'overall_mode_temp': float(mode_temp),
            'overall_std_dev_temp': float(np.std(all_temps))
        }
    
    def visualize_results(self, results, save_path=None):
        """Create visualization of leaf detection results"""
        print("📊 Creating visualization...")
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Original thermal image
        axes[0, 0].imshow(results['debug_images']['temperature_array'], 
                         cmap='hot', interpolation='nearest')
        axes[0, 0].set_title('Original Thermal Image')
        axes[0, 0].set_xlabel('X (pixels)')
        axes[0, 0].set_ylabel('Y (pixels)')
        
        # Initial temperature mask
        axes[0, 1].imshow(results['debug_images']['initial_mask'], 
                         cmap='gray', interpolation='nearest')
        axes[0, 1].set_title('Temperature Threshold Mask')
        
        # Cleaned mask
        axes[0, 2].imshow(results['debug_images']['cleaned_mask'], 
                         cmap='gray', interpolation='nearest')
        axes[0, 2].set_title('Cleaned Mask')
        
        # Labeled regions
        labeled = results['debug_images']['labeled_regions']
        axes[1, 0].imshow(labeled, cmap='tab20', interpolation='nearest')
        axes[1, 0].set_title('Connected Components')
        
        # Detected leaves overlay
        overlay = results['debug_images']['temperature_array'].copy()
        for leaf in results['leaf_analysis']['individual_leaves']:
            bbox = leaf['bounding_box']
            # Draw bounding box (simplified - would need actual mask for full overlay)
            axes[1, 1].add_patch(plt.Rectangle((bbox[0], bbox[1]), 
                                             bbox[2]-bbox[0], bbox[3]-bbox[1],
                                             fill=False, edgecolor='red', linewidth=2))
            # Add leaf ID
            axes[1, 1].text(bbox[0], bbox[1]-5, f"L{leaf['leaf_id']}", 
                           color='red', fontsize=8, fontweight='bold')
        
        axes[1, 1].imshow(overlay, cmap='hot', interpolation='nearest')
        axes[1, 1].set_title(f"Detected Leaves ({results['leaf_analysis']['total_leaves_detected']})")
        
        # Temperature distribution
        if results['leaf_analysis']['individual_leaves']:
            leaf_temps = [leaf['mean_temp'] for leaf in results['leaf_analysis']['individual_leaves']]
            axes[1, 2].hist(leaf_temps, bins=10, alpha=0.7, color='green')
            axes[1, 2].set_xlabel('Mean Leaf Temperature (°C)')
            axes[1, 2].set_ylabel('Number of Leaves')
            axes[1, 2].set_title('Leaf Temperature Distribution')
        else:
            axes[1, 2].text(0.5, 0.5, 'No leaves detected', 
                           ha='center', va='center', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('No Leaves Detected')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"💾 Visualization saved to {save_path}")
        
        plt.show()
        
        # Print summary
        print("\n📋 Detection Summary:")
        print(f"   Total leaves detected: {results['leaf_analysis']['total_leaves_detected']}")
        if results['population_statistics']['total_leaves'] > 0:
            pop = results['population_statistics']
            print(f"   Temperature range: {pop['overall_min_temp']:.1f}°C - {pop['overall_max_temp']:.1f}°C")
            print(f"   Mean temperature: {pop['overall_mean_temp']:.1f}°C")
            print(f"   Temperature std dev: {pop['overall_std_dev_temp']:.1f}°C")

def test_with_sample_data():
    """Test leaf detection with synthetic thermal data"""
    print("🧪 Testing leaf detection with synthetic data...")
    
    # Create synthetic thermal image (160x120 like tCam-Mini)
    height, width = 120, 160
    
    # Background temperature
    background = np.random.normal(20.0, 1.0, (height, width))
    
    # Add some "leaves" as warmer regions
    leaf_temp = 25.0
    
    # Leaf 1: Elliptical region
    y1, x1 = np.ogrid[:height, :width]
    leaf1_mask = ((x1 - 40)**2 / 15**2 + (y1 - 30)**2 / 10**2) <= 1
    background[leaf1_mask] = np.random.normal(leaf_temp, 0.5, np.sum(leaf1_mask))
    
    # Leaf 2: Another elliptical region
    leaf2_mask = ((x1 - 80)**2 / 12**2 + (y1 - 50)**2 / 8**2) <= 1
    background[leaf2_mask] = np.random.normal(leaf_temp + 1, 0.5, np.sum(leaf2_mask))
    
    # Leaf 3: Irregular region
    leaf3_mask = ((x1 - 120)**2 / 10**2 + (y1 - 70)**2 / 15**2) <= 1
    background[leaf3_mask] = np.random.normal(leaf_temp - 0.5, 0.5, np.sum(leaf3_mask))
    
    thermal_image = background
    
    # Test detection
    detector = LeafDetector()
    results = detector.detect_leaves(thermal_image, thermal_image)
    
    # Visualize results
    detector.visualize_results(results, 'test_leaf_detection.png')
    
    # Save results
    with open('test_detection_results.json', 'w') as f:
        # Remove debug images for JSON serialization
        save_results = results.copy()
        del save_results['debug_images']
        json.dump(save_results, f, indent=2)
    
    print("✅ Test complete! Check test_leaf_detection.png and test_detection_results.json")

if __name__ == "__main__":
    test_with_sample_data()