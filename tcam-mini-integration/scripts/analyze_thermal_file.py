#!/usr/bin/env python3
"""
Analyze Thermal Image Files

This script can analyze thermal image files (PNG, NPY, or JSON) and create
comprehensive segmentation visualizations.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import json
import argparse
import os
from datetime import datetime
from thermal_segmentation_analyzer import ThermalSegmentationAnalyzer

class ThermalFileAnalyzer(ThermalSegmentationAnalyzer):
    def __init__(self):
        # Initialize without tCam connection
        self.params = {
            'temp_threshold_offset': 1.5,
            'min_region_area': 30,
            'max_region_area': 1500,
            'morph_kernel_size': 3,
            'opening_iterations': 1,
            'closing_iterations': 2,
        }
        print("📁 Thermal File Analyzer initialized")
    
    def analyze_file(self, file_path, output_dir="thermal_analysis"):
        """Analyze thermal image from file"""
        
        print(f"📂 Loading thermal data from: {file_path}")
        
        # Load thermal data based on file extension
        thermal_data = self._load_thermal_file(file_path)
        if thermal_data is None:
            print("❌ Failed to load thermal data")
            return None
        
        print(f"✅ Loaded thermal data: {thermal_data.shape}")
        print(f"   Temperature range: {thermal_data.min():.1f}°C - {thermal_data.max():.1f}°C")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Perform segmentation analysis
        results = self._analyze_thermal_image(thermal_data)
        
        # Create comprehensive visualization
        viz_path = os.path.join(output_dir, f"{base_name}_segmentation_{timestamp}.png")
        self._create_comprehensive_visualization(thermal_data, results, viz_path)
        
        # Save detailed results
        json_path = os.path.join(output_dir, f"{base_name}_analysis_{timestamp}.json")
        self._save_file_analysis_results(file_path, thermal_data, results, json_path)
        
        print(f"📊 Analysis complete!")
        print(f"   Visualization: {viz_path}")
        print(f"   Data: {json_path}")
        
        return results
    
    def _load_thermal_file(self, file_path):
        """Load thermal data from various file formats"""
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.npy':
                # NumPy array file
                thermal_data = np.load(file_path)
                print(f"📊 Loaded NumPy array: {thermal_data.shape}, dtype: {thermal_data.dtype}")
                return thermal_data.astype(np.float32)
            
            elif file_ext == '.json':
                # JSON file with thermal data
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                if 'thermal_data' in data:
                    thermal_array = np.array(data['thermal_data'], dtype=np.float32)
                elif 'pixels' in data:
                    # Raw pixel data from tCam
                    raw_pixels = np.array(data['pixels'], dtype=np.float32)
                    if len(raw_pixels) == 19200:  # 160x120
                        thermal_array = raw_pixels.reshape(120, 160)
                        # Convert from Kelvin*100 to Celsius if needed
                        if thermal_array.max() > 1000:  # Likely Kelvin*100 format
                            thermal_array = (thermal_array * 0.01) - 273.15
                    else:
                        print(f"❌ Unexpected pixel array size: {len(raw_pixels)}")
                        return None
                elif 'temperature_data' in data:
                    thermal_array = np.array(data['temperature_data'], dtype=np.float32)
                else:\n                    print(\"❌ No recognized thermal data format in JSON\")\n                    print(f\"   Available keys: {list(data.keys())}\")\n                    return None\n                \n                print(f\"📊 Loaded JSON thermal data: {thermal_array.shape}\")\n                return thermal_array\n            \n            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:\n                # Image file - assume it's a thermal image visualization\n                # This is tricky since we need actual temperature data, not just the visualization\n                print(\"⚠️ Warning: Loading image file as thermal data\")\n                print(\"   This assumes the image represents temperature values\")\n                \n                img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)\n                if img is None:\n                    print(f\"❌ Could not load image: {file_path}\")\n                    return None\n                \n                # Convert to float and scale to reasonable temperature range\n                # This is a rough approximation - real thermal data would be better\n                thermal_data = img.astype(np.float32)\n                # Scale from 0-255 to approximately 15-35°C (typical room temperature range)\n                thermal_data = 15.0 + (thermal_data / 255.0) * 20.0\n                \n                print(f\"📊 Converted image to thermal data: {thermal_data.shape}\")\n                print(f\"   ⚠️ Note: This is an approximation, not real thermal data\")\n                return thermal_data\n            \n            else:\n                print(f\"❌ Unsupported file format: {file_ext}\")\n                print(\"   Supported formats: .npy, .json, .png, .jpg, .jpeg, .tiff, .bmp\")\n                return None\n                \n        except Exception as e:\n            print(f\"❌ Error loading file: {e}\")\n            return None\n    \n    def _save_file_analysis_results(self, file_path, thermal_data, results, save_path):\n        \"\"\"Save analysis results for file-based analysis\"\"\"\n        \n        # Calculate overall statistics\n        valid_temps = thermal_data[thermal_data >= 0]\n        \n        analysis_data = {\n            'timestamp': datetime.now().isoformat(),\n            'source_file': {\n                'path': os.path.abspath(file_path),\n                'filename': os.path.basename(file_path),\n                'file_size_bytes': os.path.getsize(file_path)\n            },\n            'image_statistics': {\n                'total_pixels': int(thermal_data.size),\n                'valid_pixels': int(len(valid_temps)),\n                'invalid_pixels': int(thermal_data.size - len(valid_temps)),\n                'temp_range': [float(np.min(valid_temps)), float(np.max(valid_temps))],\n                'mean_temp': float(np.mean(valid_temps)),\n                'median_temp': float(np.median(valid_temps)),\n                'std_temp': float(np.std(valid_temps)),\n                'image_shape': thermal_data.shape\n            },\n            'processing_parameters': self.params,\n            'processing_steps': results['processing_steps'],\n            'segmentation_results': {\n                'total_regions_detected': len(results['regions']),\n                'regions': results['regions']\n            }\n        }\n        \n        # Add population statistics if regions found\n        if results['regions']:\n            all_temps = [r['mean_temp'] for r in results['regions']]\n            all_areas = [r['area'] for r in results['regions']]\n            \n            analysis_data['population_statistics'] = {\n                'temperature_range': [min(all_temps), max(all_temps)],\n                'mean_temperature': float(np.mean(all_temps)),\n                'temperature_std': float(np.std(all_temps)),\n                'total_segmented_area': sum(all_areas),\n                'mean_region_size': float(np.mean(all_areas)),\n                'coverage_percentage': float(sum(all_areas) / thermal_data.size * 100)\n            }\n        \n        with open(save_path, 'w') as f:\n            json.dump(analysis_data, f, indent=2)\n        \n        print(f\"💾 Analysis results saved to {save_path}\")\n        \n        # Print summary\n        self._print_analysis_summary(analysis_data)\n\ndef main():\n    parser = argparse.ArgumentParser(description='Analyze thermal image files')\n    parser.add_argument('file_path', help='Path to thermal image file (.npy, .json, .png, etc.)')\n    parser.add_argument('--output', default='thermal_analysis', help='Output directory')\n    parser.add_argument('--threshold', type=float, default=1.5, help='Temperature threshold offset')\n    parser.add_argument('--min-area', type=int, default=30, help='Minimum region area')\n    parser.add_argument('--max-area', type=int, default=1500, help='Maximum region area')\n    \n    args = parser.parse_args()\n    \n    if not os.path.exists(args.file_path):\n        print(f\"❌ File not found: {args.file_path}\")\n        return\n    \n    analyzer = ThermalFileAnalyzer()\n    \n    # Update parameters if provided\n    analyzer.params['temp_threshold_offset'] = args.threshold\n    analyzer.params['min_region_area'] = args.min_area\n    analyzer.params['max_region_area'] = args.max_area\n    \n    results = analyzer.analyze_file(args.file_path, args.output)\n    \n    if results:\n        print(\"\\n✅ Analysis completed successfully!\")\n        print(f\"📁 Results saved in: {args.output}/\")\n    else:\n        print(\"\\n❌ Analysis failed\")\n\nif __name__ == \"__main__\":\n    main()
