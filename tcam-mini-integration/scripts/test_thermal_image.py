#!/usr/bin/env python3
"""
Test tCam-Mini Thermal Image Capture
Test thermal image capture from tCam-Mini on home network
"""

import socket
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
import sys

def get_thermal_image(ip, port=5001):
    """Get thermal image from tCam-Mini"""
    try:
        print(f"🔍 Getting thermal image from {ip}:{port}")
        
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((ip, port))
        print(f"✅ Connected to {ip}:{port}")
        
        # Send get_image command with STX/ETX delimiters
        command = b'\x02{"cmd": "get_image"}\x03'
        sock.send(command)
        print(f"📤 Sent: get_image command")
        
        # Receive response (may be large)
        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            if response.endswith(b'\x03'):
                break
        
        sock.close()
        print(f"📥 Received {len(response)} bytes")
        
        # Strip delimiters and parse JSON
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]  # Remove STX/ETX
        
        response_str = response.decode('utf-8', errors='ignore')
        
        try:
            data = json.loads(response_str)
            print(f"✅ JSON parsed successfully!")
            
            if 'image' in data and 'radiometric' in data['image']:
                # Decode base64 thermal data
                thermal_data = base64.b64decode(data['image']['radiometric'])
                print(f"📊 Thermal data: {len(thermal_data)} bytes")
                
                # Convert to numpy array (160x120 16-bit values)
                thermal_array = np.frombuffer(thermal_data, dtype=np.uint16)
                thermal_image = thermal_array.reshape(120, 160)
                
                # Convert to Celsius (radiometric Lepton data is Kelvin * 100)
                thermal_celsius = (thermal_image * 0.01) - 273.15
                
                print(f"🌡️  Temperature range: {thermal_celsius.min():.1f}°C to {thermal_celsius.max():.1f}°C")
                
                # Display thermal image
                plt.figure(figsize=(10, 6))
                plt.imshow(thermal_celsius, cmap='hot', interpolation='nearest')
                plt.colorbar(label='Temperature (°C)')
                plt.title(f'tCam-Mini Thermal Image - {ip}')
                plt.xlabel('Pixel X')
                plt.ylabel('Pixel Y')
                
                # Save image
                filename = f'thermal_image_{ip.replace(".", "_")}.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                print(f"💾 Saved thermal image: {filename}")
                
                plt.show()
                return True
            else:
                print(f"⚠️  No thermal image data in response")
                print(f"📋 Available keys: {list(data.keys())}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"📋 Raw response (first 200 chars): {response_str[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    ip = "192.168.1.130"
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    
    print("🎯 tCam-Mini Thermal Image Test")
    print("=" * 40)
    
    success = get_thermal_image(ip)
    
    if success:
        print("\n🎉 SUCCESS! Thermal imaging is working!")
        print("💡 Your tCam-Mini is fully functional on your home network!")
    else:
        print("\n❌ Thermal image test failed.")
