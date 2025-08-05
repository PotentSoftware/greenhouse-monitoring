#!/usr/bin/env python3
"""
Multi-Format Thermal Capture for tCam-Mini
Captures 10 sequential thermal images and saves in .npy, .tiff, and .png formats
"""

import socket
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import time
import os
from datetime import datetime
from PIL import Image
import cv2

def get_thermal_data(ip="192.168.1.130", port=5001, timeout=20):
    """Get raw thermal data from tCam-Mini"""
    try:
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        # Send get_image command
        command = b'\x02{"cmd": "get_image"}\x03'
        sock.send(command)
        
        # Receive response (may be large)
        response = sock.recv(65536)  # Larger buffer for thermal data
        
        sock.close()
        
        # Strip delimiters
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]
        
        # Parse JSON
        data = json.loads(response.decode('utf-8'))
        
        if 'radiometric' not in data:
            return None, None
        
        # Decode base64 thermal data
        thermal_data = base64.b64decode(data['radiometric'])
        
        # Convert to numpy array (160x120 16-bit values)
        thermal_array = np.frombuffer(thermal_data, dtype=np.uint16)
        thermal_array = thermal_array.reshape((120, 160))
        
        # Convert from Kelvin*100 to Celsius
        temp_celsius = (thermal_array * 0.01) - 273.15
        
        return thermal_array, temp_celsius
        
    except Exception as e:
        print(f"❌ Error getting thermal data: {e}")
        return None, None

def save_thermal_image_formats(raw_data, temp_celsius, base_filename, desktop_path):
    """Save thermal data in all three formats"""
    
    # 1. Save as .npy (raw numpy data)
    npy_path = os.path.join(desktop_path, f"{base_filename}.npy")
    np.save(npy_path, temp_celsius)
    
    # 2. Save as .tiff (16-bit temperature data)
    tiff_path = os.path.join(desktop_path, f"{base_filename}.tiff")
    # Convert to 16-bit integer (temperature * 100 for precision)
    temp_int16 = (temp_celsius * 100).astype(np.int16)
    Image.fromarray(temp_int16, mode='I;16').save(tiff_path)
    
    # 3. Save as .png (colorized thermal image)
    png_path = os.path.join(desktop_path, f"{base_filename}.png")
    
    # Create thermal colormap
    colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
             '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
    thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
    
    # Create figure without displaying
    plt.figure(figsize=(8, 6))
    plt.imshow(temp_celsius, cmap=thermal_cmap, aspect='equal')
    plt.colorbar(label='Temperature (°C)')
    plt.title(f'Thermal Image - {base_filename}')
    plt.xlabel('Pixel X')
    plt.ylabel('Pixel Y')
    
    # Add temperature statistics as text
    min_temp = temp_celsius.min()
    max_temp = temp_celsius.max()
    mean_temp = temp_celsius.mean()
    
    plt.text(0.02, 0.98, f'Min: {min_temp:.1f}°C\nMax: {max_temp:.1f}°C\nMean: {mean_temp:.1f}°C', 
             transform=plt.gca().transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches='tight')
    plt.close()  # Close figure to free memory
    
    return npy_path, tiff_path, png_path

def capture_sequential_thermal_images(num_images=10, ip="192.168.1.130", port=5001):
    """Capture multiple sequential thermal images in all formats"""
    
    # Ensure Desktop directory exists
    desktop_path = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)
        print(f"📁 Created Desktop directory: {desktop_path}")
    
    print("🎯 Multi-Format Thermal Image Capture")
    print("=" * 50)
    print(f"📸 Capturing {num_images} sequential thermal images")
    print(f"💾 Saving to: {desktop_path}")
    print(f"📁 Formats: .npy (raw data), .tiff (16-bit), .png (colorized)")
    print()
    
    successful_captures = 0
    failed_captures = 0
    
    # Create timestamp for this capture session
    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i in range(1, num_images + 1):
        print(f"📷 Capturing image {i}/{num_images}...", end=" ")
        
        # Get thermal data
        raw_data, temp_celsius = get_thermal_data(ip, port)
        
        if raw_data is not None and temp_celsius is not None:
            # Create filename with session timestamp and sequence number
            base_filename = f"thermal_{session_timestamp}_{i:02d}"
            
            try:
                # Save in all formats
                npy_path, tiff_path, png_path = save_thermal_image_formats(
                    raw_data, temp_celsius, base_filename, desktop_path)
                
                # Display statistics
                min_temp = temp_celsius.min()
                max_temp = temp_celsius.max()
                mean_temp = temp_celsius.mean()
                
                print(f"✅ Success! ({min_temp:.1f}°C - {max_temp:.1f}°C, avg: {mean_temp:.1f}°C)")
                successful_captures += 1
                
            except Exception as e:
                print(f"❌ Save failed: {e}")
                failed_captures += 1
        else:
            print("❌ Capture failed!")
            failed_captures += 1
        
        # Brief pause between captures (except for last one)
        if i < num_images:
            time.sleep(0.5)
    
    print()
    print("📊 CAPTURE SUMMARY")
    print("=" * 25)
    print(f"✅ Successful: {successful_captures}")
    print(f"❌ Failed: {failed_captures}")
    print(f"📁 Location: {desktop_path}")
    
    if successful_captures > 0:
        print()
        print("📋 FILES CREATED:")
        print(f"   • {successful_captures} × .npy files (raw temperature data)")
        print(f"   • {successful_captures} × .tiff files (16-bit temperature)")
        print(f"   • {successful_captures} × .png files (colorized thermal images)")
        print()
        print("🔍 File naming pattern:")
        print(f"   thermal_{session_timestamp}_XX.[npy|tiff|png]")
    
    return successful_captures, failed_captures

def interactive_capture():
    """Interactive thermal capture with user prompts"""
    print("🌡️  tCam-Mini Multi-Format Thermal Capture")
    print("=" * 50)
    print()
    
    # Get number of images
    while True:
        try:
            num_images = input("📸 How many images to capture? (default: 10): ").strip()
            if not num_images:
                num_images = 10
            else:
                num_images = int(num_images)
            
            if num_images < 1 or num_images > 100:
                print("⚠️  Please enter a number between 1 and 100")
                continue
            break
        except ValueError:
            print("⚠️  Please enter a valid number")
    
    print()
    print(f"🎯 Ready to capture {num_images} thermal images")
    print("📁 Files will be saved to ~/Desktop in .npy, .tiff, and .png formats")
    print()
    
    input("⏳ Press ENTER to start capture...")
    print()
    
    # Start capture
    successful, failed = capture_sequential_thermal_images(num_images)
    
    print()
    if successful == num_images:
        print("🎉 All captures completed successfully!")
    elif successful > 0:
        print(f"⚠️  {successful} of {num_images} captures successful")
    else:
        print("❌ All captures failed - check tCam-Mini connection")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            num_images = int(sys.argv[1])
            capture_sequential_thermal_images(num_images)
        except ValueError:
            print("Usage: python3 multi_format_thermal_capture.py [number_of_images]")
    else:
        interactive_capture()
