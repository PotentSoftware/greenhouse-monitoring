#!/usr/bin/env python3
"""
Test Temperature Conversion for tCam-Mini
Verifies that raw Lepton data is properly converted to Celsius
"""

import socket
import json
import base64
import numpy as np

def raw_to_celsius(raw_data, resolution=0.01):
    """Convert raw Lepton thermal data to Celsius
    Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
    """
    celsius_data = (raw_data.astype(float) * resolution) - 273.15
    return celsius_data

def test_temperature_conversion():
    """Test temperature conversion with real tCam data"""
    print("🌡️  tCam-Mini Temperature Conversion Test")
    print("=" * 50)
    
    try:
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(('192.168.1.130', 5001))
        
        # Send get_image command
        cmd_json = json.dumps({"cmd": "get_image"})
        cmd_with_delimiters = b'\x02' + cmd_json.encode() + b'\x03'
        sock.send(cmd_with_delimiters)
        
        # Receive response
        response = b''
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            response += chunk
            if b'\x03' in chunk:
                break
        
        sock.close()
        
        # Parse response
        response_str = response.decode().strip('\x02\x03')
        data = json.loads(response_str)
        
        if 'radiometric' in data:
            # Decode image data
            img_data = base64.b64decode(data['radiometric'])
            thermal_array = np.frombuffer(img_data, dtype=np.uint16)
            thermal_raw = thermal_array.reshape((120, 160))
            
            # Convert to Celsius
            thermal_celsius = raw_to_celsius(thermal_raw)
            
            # Display statistics
            print(f"📊 Raw Data Statistics:")
            print(f"   Min Raw: {thermal_raw.min()}")
            print(f"   Max Raw: {thermal_raw.max()}")
            print(f"   Avg Raw: {thermal_raw.mean():.1f}")
            print(f"   Raw values are in Kelvin × 100")
            print()
            
            print(f"🌡️  Temperature Statistics (°C):")
            print(f"   Min Temp: {thermal_celsius.min():.1f}°C")
            print(f"   Max Temp: {thermal_celsius.max():.1f}°C")
            print(f"   Avg Temp: {thermal_celsius.mean():.1f}°C")
            print(f"   Range: {thermal_celsius.max() - thermal_celsius.min():.1f}°C")
            print()
            
            # Test specific pixels
            center_y, center_x = 60, 80  # Center of 120x160 image
            corner_y, corner_x = 10, 10  # Corner pixel
            
            print(f"🎯 Sample Pixel Temperatures:")
            print(f"   Center pixel ({center_x},{center_y}): {thermal_celsius[center_y, center_x]:.1f}°C")
            print(f"   Corner pixel ({corner_x},{corner_y}): {thermal_celsius[corner_y, corner_x]:.1f}°C")
            print()
            
            # Validate temperature range (should be reasonable for indoor/outdoor use)
            if thermal_celsius.min() < -40 or thermal_celsius.max() > 100:
                print("⚠️  Warning: Temperature range seems unusual for typical use")
                print("   This may indicate calibration issues or extreme conditions")
            else:
                print("✅ Temperature range appears reasonable for thermal imaging")
            
            print()
            print("📋 Radiometric Conversion Used:")
            print(f"   Formula: T(°C) = (raw × 0.01) - 273.15")
            print(f"   Raw data: Kelvin × 100 (radiometric Lepton sensor)")
            print(f"   Resolution: 0.01 K per raw unit")
            print()
            print("💡 Note: This conversion is for radiometric Lepton sensors.")
            print("   The tCam-Mini uses radiometric sensors that provide")
            print("   absolute temperature measurements.")
            
        else:
            print("❌ No thermal data received")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_temperature_conversion()
