#!/usr/bin/env python3
"""
Analyze captured tCam-Mini data offline
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

CAPTURES_DIR = "/home/lio/github/greenhouse-monitoring/tcam-mini-integration/captures"

def find_latest_session():
    """Find the most recent capture session"""
    sessions = [d for d in os.listdir(CAPTURES_DIR) if d.startswith("session_")]
    if not sessions:
        return None
    return os.path.join(CAPTURES_DIR, sorted(sessions)[-1])

def analyze_thermal_data(session_dir):
    """Analyze thermal pixel data"""
    print("\n📊 Thermal Data Analysis")
    print("=" * 40)
    
    # Check for thermal pixels file
    pixels_file = os.path.join(session_dir, "thermal_pixels.json")
    if os.path.exists(pixels_file):
        with open(pixels_file, 'r') as f:
            data = json.load(f)
            pixels = data["pixels"]
            
        print(f"✅ Found thermal pixel data")
        print(f"   Total pixels: {len(pixels)}")
        
        # Filter out negative values (faulty pixels)
        valid_pixels = [p for p in pixels if p >= 0]
        invalid_count = len(pixels) - len(valid_pixels)
        
        if invalid_count > 0:
            print(f"   ⚠️  Faulty pixels detected: {invalid_count}")
        
        # Statistics
        print(f"\n📈 Temperature Statistics (valid pixels only):")
        print(f"   Min: {min(valid_pixels):.2f}°C")
        print(f"   Max: {max(valid_pixels):.2f}°C")
        print(f"   Mean: {np.mean(valid_pixels):.2f}°C")
        print(f"   Median: {np.median(valid_pixels):.2f}°C")
        print(f"   Std Dev: {np.std(valid_pixels):.2f}°C")
        
        # Expected dimensions for Lepton 3.5
        if len(pixels) == 19200:  # 160x120
            thermal_array = np.array(pixels).reshape(120, 160)
            print(f"\n🖼️  Image dimensions: 160x120 (Lepton 3.5)")
            return thermal_array
        elif len(pixels) == 4800:  # 80x60
            thermal_array = np.array(pixels).reshape(60, 80)
            print(f"\n🖼️  Image dimensions: 80x60 (Lepton 2.5)")
            return thermal_array
        else:
            print(f"\n⚠️  Unexpected pixel count for standard Lepton sensor")
            # Try to find best dimensions
            factors = []
            for i in range(1, int(np.sqrt(len(pixels))) + 1):
                if len(pixels) % i == 0:
                    factors.append((i, len(pixels) // i))
            print(f"   Possible dimensions: {factors[-5:]}")
    else:
        print("❌ No thermal pixel data found")
    
    return None

def analyze_thermal_frames(session_dir):
    """Analyze multiple thermal frames"""
    frames_file = os.path.join(session_dir, "thermal_frames.json")
    if not os.path.exists(frames_file):
        return
    
    print("\n📸 Thermal Frames Analysis")
    print("=" * 40)
    
    with open(frames_file, 'r') as f:
        frames_data = json.load(f)
    
    print(f"✅ Found {len(frames_data)} thermal frames")
    
    # Analyze frame-to-frame variation
    if len(frames_data) > 1:
        frame_means = []
        for frame in frames_data:
            pixels = frame["pixels"]
            valid_pixels = [p for p in pixels if p >= 0]
            if valid_pixels:
                frame_means.append(np.mean(valid_pixels))
        
        if frame_means:
            print(f"\n📈 Frame-to-frame statistics:")
            print(f"   Mean temperature variation: {np.std(frame_means):.3f}°C")
            print(f"   Temperature range: {min(frame_means):.2f}°C - {max(frame_means):.2f}°C")

def visualize_thermal_image(thermal_array, session_dir):
    """Create and save thermal visualization"""
    if thermal_array is None:
        return
    
    print("\n🎨 Creating thermal visualization...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('tCam-Mini Thermal Analysis', fontsize=16)
    
    # 1. Raw thermal image
    im1 = axes[0, 0].imshow(thermal_array, cmap='jet', interpolation='nearest')
    axes[0, 0].set_title('Raw Thermal Image')
    axes[0, 0].axis('off')
    plt.colorbar(im1, ax=axes[0, 0], label='Temperature (°C)')
    
    # 2. Histogram
    valid_pixels = thermal_array[thermal_array >= 0].flatten()
    axes[0, 1].hist(valid_pixels, bins=50, color='blue', alpha=0.7)
    axes[0, 1].set_title('Temperature Distribution')
    axes[0, 1].set_xlabel('Temperature (°C)')
    axes[0, 1].set_ylabel('Pixel Count')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Contour plot for potential leaf detection
    axes[1, 0].contour(thermal_array, levels=10, colors='black', alpha=0.3)
    im3 = axes[1, 0].contourf(thermal_array, levels=20, cmap='RdYlBu_r')
    axes[1, 0].set_title('Temperature Contours (Leaf Detection)')
    axes[1, 0].axis('off')
    plt.colorbar(im3, ax=axes[1, 0], label='Temperature (°C)')
    
    # 4. Enhanced contrast visualization
    # Normalize and enhance contrast
    normalized = (thermal_array - np.min(thermal_array)) / (np.max(thermal_array) - np.min(thermal_array))
    enhanced = np.power(normalized, 0.5)  # Gamma correction
    
    # Show enhanced contrast image
    axes[1, 1].imshow(enhanced, cmap='gray')
    axes[1, 1].set_title('Enhanced Contrast (Leaf Boundaries)')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    
    # Save figure
    output_file = os.path.join(session_dir, "thermal_analysis.png")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   💾 Saved visualization: {output_file}")
    plt.close()

def analyze_api_responses(session_dir):
    """Analyze API endpoint responses"""
    summary_file = os.path.join(session_dir, "capture_summary.json")
    if not os.path.exists(summary_file):
        return
    
    print("\n🔍 API Endpoint Analysis")
    print("=" * 40)
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    for result in summary["results"]:
        if result["success"]:
            print(f"\n✅ {result['endpoint']} ({result['path']}):")
            if result["data_type"] == "json" and "data" in result:
                data = result["data"]
                # Show key information based on endpoint
                if result["endpoint"] == "status":
                    print(f"   WiFi Mode: {data.get('wifi_mode', 'unknown')}")
                    print(f"   IP Address: {data.get('ip', 'unknown')}")
                    print(f"   Temperature: {data.get('temperature', 'unknown')}")
                elif result["endpoint"] == "config":
                    print(f"   SSID: {data.get('ssid', 'unknown')}")
                    print(f"   Emissivity: {data.get('emissivity', 'unknown')}")
                elif result["endpoint"] == "info":
                    print(f"   Version: {data.get('version', 'unknown')}")
                    print(f"   Model: {data.get('model', 'unknown')}")
                # Show first few keys for other endpoints
                else:
                    keys = list(data.keys())[:5]
                    print(f"   Keys: {', '.join(keys)}")

def main():
    print("🔬 tCam-Mini Capture Analysis")
    print("=" * 50)
    
    # Find latest session or use command line argument
    import sys
    if len(sys.argv) > 1:
        session_dir = sys.argv[1]
    else:
        session_dir = find_latest_session()
    
    if not session_dir or not os.path.exists(session_dir):
        print("❌ No capture sessions found")
        print(f"   Looking in: {CAPTURES_DIR}")
        return
    
    print(f"📁 Analyzing session: {os.path.basename(session_dir)}")
    
    # Analyze API responses
    analyze_api_responses(session_dir)
    
    # Analyze thermal data
    thermal_array = analyze_thermal_data(session_dir)
    
    # Analyze thermal frames
    analyze_thermal_frames(session_dir)
    
    # Create visualizations
    if thermal_array is not None:
        visualize_thermal_image(thermal_array, session_dir)
    
    print("\n✅ Analysis complete!")
    print(f"📁 Results saved in: {session_dir}")

if __name__ == "__main__":
    main()
