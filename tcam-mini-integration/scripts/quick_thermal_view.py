#!/usr/bin/env python3
"""
Quick Thermal Image Viewer
Captures and displays a single thermal image from tCam-Mini
"""

import socket
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import time

def get_thermal_image(ip="192.168.1.130", port=5001):
    """Get thermal image from tCam-Mini"""
    try:
        print(f"🔍 Getting thermal image from {ip}:{port}")
        
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        
        # Send get_image command
        command = b'\x02{"cmd": "get_image"}\x03'
        sock.send(command)
        
        # Receive response (may be large)
        response = b''
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            response += chunk
            if response.endswith(b'\x03'):
                break
        
        sock.close()
        
        # Strip delimiters
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]
        
        # Parse JSON
        data = json.loads(response.decode('utf-8'))
        
        if 'radiometric' not in data:
            print("❌ No radiometric data in response")
            return False
        
        # Decode base64 thermal data
        thermal_data = base64.b64decode(data['radiometric'])
        
        # Convert to numpy array (160x120 16-bit values)
        thermal_array = np.frombuffer(thermal_data, dtype=np.uint16)
        thermal_array = thermal_array.reshape((120, 160))
        
        # Convert from Kelvin*100 to Celsius
        temp_celsius = (thermal_array * 0.01) - 273.15
        
        # Display statistics
        print(f"📊 Temperature Statistics:")
        print(f"   Min: {temp_celsius.min():.1f}°C")
        print(f"   Max: {temp_celsius.max():.1f}°C")
        print(f"   Mean: {temp_celsius.mean():.1f}°C")
        
        # Create thermal colormap
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        n_bins = 256
        thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=n_bins)
        
        # Display thermal image
        plt.figure(figsize=(12, 8))
        
        # Main thermal image
        plt.subplot(1, 2, 1)
        im = plt.imshow(temp_celsius, cmap=thermal_cmap, aspect='equal')
        plt.colorbar(im, label='Temperature (°C)')
        plt.title('Thermal Image')
        plt.xlabel('Pixel X')
        plt.ylabel('Pixel Y')
        
        # Temperature histogram
        plt.subplot(1, 2, 2)
        plt.hist(temp_celsius.flatten(), bins=50, alpha=0.7, color='blue')
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Pixel Count')
        plt.title('Temperature Distribution')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save image
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"thermal_image_{timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"💾 Saved thermal image: {filename}")
        
        plt.show()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 tCam-Mini Quick Thermal Viewer")
    print("=" * 40)
    
    success = get_thermal_image()
    
    if success:
        print("✅ Thermal image captured successfully!")
    else:
        print("❌ Failed to capture thermal image.")
