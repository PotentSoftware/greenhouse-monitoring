#!/usr/bin/env python3
"""
Thermal Image Statistical Analysis Module
Performs comprehensive statistical analysis on collected thermal images including:
- Central tendency measures (mean, median, mode, standard deviation)
- Principal Component Analysis (PCA)
- Visualization generation (histograms, box plots, PCA plots)
"""

import os
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import base64
from io import BytesIO

# Scientific computing and statistics
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Visualization libraries
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns

# Set style for better-looking plots
plt.style.use('dark_background')
sns.set_palette("husl")

class ThermalImageAnalyzer:
    """Statistical analysis and visualization for thermal image collections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_image_collection(self, collection_path: str) -> Dict:
        """
        Perform comprehensive statistical analysis on a thermal image collection
        
        Args:
            collection_path: Path to the thermal image collection directory
            
        Returns:
            Dictionary containing analysis results and visualization data
        """
        try:
            # Load all thermal images from the collection
            images, metadata = self._load_image_collection(collection_path)
            
            if len(images) == 0:
                raise ValueError("No thermal images found in collection")
            
            # Perform statistical analysis
            stats_results = self._calculate_comprehensive_statistics(images)
            
            # Perform Principal Component Analysis
            pca_results = self._perform_pca_analysis(images)
            
            # Generate visualizations
            visualizations = self._generate_visualizations(images, stats_results, pca_results)
            
            # Compile comprehensive results
            analysis_results = {
                'collection_info': {
                    'path': collection_path,
                    'num_images': len(images),
                    'image_shape': images[0].shape,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'metadata': metadata
                },
                'statistical_analysis': stats_results,
                'pca_analysis': pca_results,
                'visualizations': visualizations
            }
            
            self.logger.info(f"✅ Analysis complete for {len(images)} thermal images")
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed: {str(e)}")
            raise
    
    def _load_image_collection(self, collection_path: str) -> Tuple[List[np.ndarray], Dict]:
        """Load all .npy thermal images from collection directory"""
        images = []
        metadata = {}
        
        # Load metadata if available
        metadata_path = os.path.join(collection_path, 'collection_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Load all .npy image files
        for filename in sorted(os.listdir(collection_path)):
            if filename.endswith('.npy'):
                image_path = os.path.join(collection_path, filename)
                thermal_image = np.load(image_path)
                images.append(thermal_image)
                
        self.logger.info(f"📁 Loaded {len(images)} thermal images from {collection_path}")
        return images, metadata
    
    def _calculate_comprehensive_statistics(self, images: List[np.ndarray]) -> Dict:
        """Calculate comprehensive statistical measures for the image collection"""
        
        # Flatten all images for global statistics
        all_pixels = np.concatenate([img.flatten() for img in images])
        
        # Per-image statistics
        per_image_stats = []
        for i, img in enumerate(images):
            img_stats = {
                'image_index': i,
                'mean': float(np.mean(img)),
                'median': float(np.median(img)),
                'std': float(np.std(img)),
                'min': float(np.min(img)),
                'max': float(np.max(img)),
                'q25': float(np.percentile(img, 25)),
                'q75': float(np.percentile(img, 75))
            }
            
            # Calculate mode (most frequent temperature bin)
            hist, bin_edges = np.histogram(img.flatten(), bins=50)
            mode_bin = np.argmax(hist)
            img_stats['mode'] = float((bin_edges[mode_bin] + bin_edges[mode_bin + 1]) / 2)
            
            per_image_stats.append(img_stats)
        
        # Global collection statistics
        global_stats = {
            'mean': float(np.mean(all_pixels)),
            'median': float(np.median(all_pixels)),
            'std': float(np.std(all_pixels)),
            'min': float(np.min(all_pixels)),
            'max': float(np.max(all_pixels)),
            'q25': float(np.percentile(all_pixels, 25)),
            'q75': float(np.percentile(all_pixels, 75)),
            'skewness': float(stats.skew(all_pixels)),
            'kurtosis': float(stats.kurtosis(all_pixels))
        }
        
        # Calculate mode for global data
        hist, bin_edges = np.histogram(all_pixels, bins=100)
        mode_bin = np.argmax(hist)
        global_stats['mode'] = float((bin_edges[mode_bin] + bin_edges[mode_bin + 1]) / 2)
        
        # Temperature distribution analysis
        temp_ranges = {
            'very_cold': float(np.sum(all_pixels < 15)),
            'cold': float(np.sum((all_pixels >= 15) & (all_pixels < 20))),
            'moderate': float(np.sum((all_pixels >= 20) & (all_pixels < 25))),
            'warm': float(np.sum((all_pixels >= 25) & (all_pixels < 30))),
            'hot': float(np.sum(all_pixels >= 30))
        }
        
        return {
            'global_statistics': global_stats,
            'per_image_statistics': per_image_stats,
            'temperature_distribution': temp_ranges,
            'total_pixels': len(all_pixels)
        }
    
    def _perform_pca_analysis(self, images: List[np.ndarray]) -> Dict:
        """Perform Principal Component Analysis on the thermal image collection"""
        
        # Reshape images to 2D array (samples x features)
        image_shape = images[0].shape
        flattened_images = np.array([img.flatten() for img in images])
        
        # Standardize the data
        scaler = StandardScaler()
        standardized_images = scaler.fit_transform(flattened_images)
        
        # Perform PCA
        pca = PCA()
        pca_result = pca.fit_transform(standardized_images)
        
        # Calculate explained variance ratios
        explained_variance = pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)
        
        # Find number of components for 95% variance
        n_components_95 = np.argmax(cumulative_variance >= 0.95) + 1
        
        return {
            'n_components': len(explained_variance),
            'explained_variance_ratio': explained_variance.tolist(),
            'cumulative_variance_ratio': cumulative_variance.tolist(),
            'n_components_95_variance': int(n_components_95),
            'pca_scores': pca_result.tolist(),
            'original_shape': image_shape,
            'mean_reconstruction_error': float(np.mean(np.sum((standardized_images - pca.inverse_transform(pca_result))**2, axis=1)))
        }
    
    def _generate_visualizations(self, images: List[np.ndarray], stats_results: Dict, pca_results: Dict) -> Dict:
        """Generate comprehensive visualizations for the analysis"""
        
        visualizations = {}
        
        # 1. Temperature Distribution Histogram
        all_pixels = np.concatenate([img.flatten() for img in images])
        
        plt.figure(figsize=(12, 8))
        plt.hist(all_pixels, bins=50, alpha=0.7, color='orange', edgecolor='white')
        plt.axvline(stats_results['global_statistics']['mean'], color='red', linestyle='--', 
                   label=f"Mean: {stats_results['global_statistics']['mean']:.1f}°C")
        plt.axvline(stats_results['global_statistics']['median'], color='green', linestyle='--',
                   label=f"Median: {stats_results['global_statistics']['median']:.1f}°C")
        plt.axvline(stats_results['global_statistics']['mode'], color='blue', linestyle='--',
                   label=f"Mode: {stats_results['global_statistics']['mode']:.1f}°C")
        
        plt.xlabel('Temperature (°C)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.title('Thermal Image Temperature Distribution', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        visualizations['temperature_histogram'] = self._plot_to_base64()
        
        # 2. Box Plot of Per-Image Statistics
        per_image_means = [stat['mean'] for stat in stats_results['per_image_statistics']]
        per_image_stds = [stat['std'] for stat in stats_results['per_image_statistics']]
        per_image_medians = [stat['median'] for stat in stats_results['per_image_statistics']]
        
        plt.figure(figsize=(12, 8))
        box_data = [per_image_means, per_image_medians, per_image_stds]
        box_labels = ['Mean Temp', 'Median Temp', 'Std Dev']
        
        bp = plt.boxplot(box_data, labels=box_labels, patch_artist=True)
        colors = ['orange', 'lightblue', 'lightgreen']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        plt.ylabel('Temperature (°C)', fontsize=12)
        plt.title('Per-Image Statistical Distribution', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        visualizations['statistics_boxplot'] = self._plot_to_base64()
        
        # 3. PCA Explained Variance Plot
        plt.figure(figsize=(12, 8))
        components = range(1, len(pca_results['explained_variance_ratio']) + 1)
        
        plt.subplot(2, 1, 1)
        plt.bar(components, pca_results['explained_variance_ratio'], alpha=0.7, color='skyblue')
        plt.xlabel('Principal Component')
        plt.ylabel('Explained Variance Ratio')
        plt.title('PCA: Individual Component Variance', fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 1, 2)
        plt.plot(components, pca_results['cumulative_variance_ratio'], 'o-', color='red', linewidth=2)
        plt.axhline(y=0.95, color='green', linestyle='--', label='95% Variance')
        plt.axvline(x=pca_results['n_components_95_variance'], color='green', linestyle='--')
        plt.xlabel('Number of Components')
        plt.ylabel('Cumulative Explained Variance')
        plt.title('PCA: Cumulative Variance Explained', fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        visualizations['pca_variance_plot'] = self._plot_to_base64()
        
        # 4. PCA Scores Plot (first 2 components)
        if len(pca_results['pca_scores']) > 1:
            plt.figure(figsize=(10, 8))
            pca_scores = np.array(pca_results['pca_scores'])
            
            plt.scatter(pca_scores[:, 0], pca_scores[:, 1], 
                       c=range(len(pca_scores)), cmap='viridis', s=100, alpha=0.7)
            plt.colorbar(label='Image Index')
            plt.xlabel(f'PC1 ({pca_results["explained_variance_ratio"][0]:.1%} variance)')
            plt.ylabel(f'PC2 ({pca_results["explained_variance_ratio"][1]:.1%} variance)')
            plt.title('PCA: First Two Principal Components', fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            
            # Add image labels
            for i, (x, y) in enumerate(pca_scores[:, :2]):
                plt.annotate(f'Img{i+1}', (x, y), xytext=(5, 5), 
                           textcoords='offset points', fontsize=8)
            
            visualizations['pca_scores_plot'] = self._plot_to_base64()
        
        # 5. Temperature Range Distribution Pie Chart
        temp_dist = stats_results['temperature_distribution']
        
        plt.figure(figsize=(10, 8))
        labels = ['Very Cold (<15°C)', 'Cold (15-20°C)', 'Moderate (20-25°C)', 
                 'Warm (25-30°C)', 'Hot (>30°C)']
        sizes = [temp_dist['very_cold'], temp_dist['cold'], temp_dist['moderate'],
                temp_dist['warm'], temp_dist['hot']]
        colors = ['lightblue', 'blue', 'green', 'orange', 'red']
        
        # Only include non-zero categories
        non_zero_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors) if size > 0]
        if non_zero_data:
            labels, sizes, colors = zip(*non_zero_data)
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Temperature Range Distribution', fontsize=14, fontweight='bold')
            
            visualizations['temperature_distribution_pie'] = self._plot_to_base64()
        
        return visualizations
    
    def _plot_to_base64(self) -> str:
        """Convert current matplotlib plot to base64 string"""
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='#1e1e1e', edgecolor='none')
        buffer.seek(0)
        
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close()  # Close the figure to free memory
        
        return base64.b64encode(plot_data).decode()
    
    def get_available_collections(self, base_path: str = "~/Desktop") -> List[Dict]:
        """Get list of available thermal image collections"""
        expanded_path = os.path.expanduser(base_path)
        collections = []
        
        try:
            if not os.path.exists(expanded_path):
                return collections
                
            for item in os.listdir(expanded_path):
                item_path = os.path.join(expanded_path, item)
                if os.path.isdir(item_path) and item.startswith('thermal_collection_'):
                    # Check if directory contains .npy files
                    npy_files = [f for f in os.listdir(item_path) if f.endswith('.npy')]
                    if npy_files:
                        # Get collection metadata
                        metadata_path = os.path.join(item_path, 'collection_metadata.json')
                        metadata = {}
                        if os.path.exists(metadata_path):
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        
                        collections.append({
                            'name': item,
                            'path': item_path,
                            'num_images': len(npy_files),
                            'created': metadata.get('start_time', 'Unknown'),
                            'size_mb': sum(os.path.getsize(os.path.join(item_path, f)) 
                                         for f in os.listdir(item_path)) / (1024 * 1024)
                        })
            
            # Sort by creation time (newest first)
            collections.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error scanning collections: {str(e)}")
        
        return collections
