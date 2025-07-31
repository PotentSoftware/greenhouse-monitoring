#!/usr/bin/env python3
"""
tCam-Mini AP Mode API Test Script
Tests communication with tCam-Mini when connected to its Access Point
"""

import requests
import json
import time
from datetime import datetime
import numpy as np
import cv2

# tCam-Mini AP mode configuration
TCAM_AP_IP = "192.168.4.1"
TIMEOUT = 5

# Known API endpoints from tCam documentation
API_ENDPOINTS = {
    "status": "/status",
    "config": "/config", 
    "thermal_raw": "/thermal_raw",
    "thermal_stats": "/thermal_stats",
    "thermal_image": "/thermal_image",
    "info": "/info",
    "cmd": "/cmd"
}

def test_endpoint(endpoint_name, endpoint_path):
    """Test a single API endpoint"""
    url = f"http://{TCAM_AP_IP}{endpoint_path}"
    print(f"\n🔍 Testing {endpoint_name}: {url}")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"   ✅ JSON Response:")
                print(json.dumps(data, indent=4)[:500])  # Limit output
                return True, data
            except json.JSONDecodeError:
                # Check if it's an image
                if 'image' in response.headers.get('content-type', ''):
                    print(f"   ✅ Image Response (size: {len(response.content)} bytes)")
                    return True, response.content
                else:
                    print(f"   ✅ Text Response: {response.text[:200]}")
                    return True, response.text
        else:
            print(f"   ❌ Error: HTTP {response.status_code}")
            return False, None
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout after {TIMEOUT} seconds")
        return False, None
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection refused - Are you connected to tCam-Mini AP?")
        return False, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def get_thermal_data():
    """Get thermal data from tCam-Mini"""
    print("\n📡 Fetching thermal data...")
    
    # Try raw thermal data first
    success, raw_data = test_endpoint("Thermal Raw", "/thermal_raw")
    if success and isinstance(raw_data, dict):
        pixels = raw_data.get("pixels", [])
        if pixels:
            print(f"\n📊 Thermal Data Analysis:")
            print(f"   Total pixels: {len(pixels)}")
            print(f"   Min temp: {min(pixels):.2f}°C")
            print(f"   Max temp: {max(pixels):.2f}°C")
            print(f"   Avg temp: {np.mean(pixels):.2f}°C")
            
            # Reshape to 160x120 for Lepton 3.5
            if len(pixels) == 19200:  # 160x120
                thermal_array = np.array(pixels).reshape(120, 160)
                print(f"   Array shape: {thermal_array.shape}")
                return thermal_array
            else:
                print(f"   ⚠️  Unexpected pixel count: {len(pixels)}")
    
    return None

def save_thermal_image(thermal_array):
    """Save thermal array as image"""
    if thermal_array is None:
        return
    
    # Normalize to 0-255 for visualization
    normalized = ((thermal_array - thermal_array.min()) / 
                  (thermal_array.max() - thermal_array.min()) * 255).astype(np.uint8)
    
    # Apply colormap
    colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
    
    # Save image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/home/lio/github/greenhouse-monitoring/tcam-mini-integration/thermal_captures/thermal_{timestamp}.png"
    cv2.imwrite(filename, colored)
    print(f"\n💾 Thermal image saved: {filename}")

def main():
    print("🎯 tCam-Mini AP Mode API Test")
    print("=" * 50)
    print(f"📡 Target IP: {TCAM_AP_IP}")
    print(f"⏱️  Timeout: {TIMEOUT} seconds")
    print("\n⚠️  Make sure you are connected to the tCam-Mini AP network!")
    print("   Network name: tCam-Mini-CDE9")
    print("=" * 50)
    
    # Test connectivity
    print(f"\n🔗 Testing connectivity to {TCAM_AP_IP}...")
    try:
        response = requests.get(f"http://{TCAM_AP_IP}/", timeout=2)
        print("   ✅ tCam-Mini is reachable!")
    except:
        print("   ❌ Cannot reach tCam-Mini. Please check:")
        print("      1. Connect to WiFi network: tCam-Mini-CDE9")
        print("      2. Verify IP address: 192.168.4.1")
        print("      3. Make sure tCam-Mini is powered on")
        return
    
    # Test all endpoints
    results = {}
    for name, path in API_ENDPOINTS.items():
        success, data = test_endpoint(name, path)
        results[name] = {"success": success, "data": data}
        time.sleep(0.5)  # Be nice to the device
    
    # Get and analyze thermal data
    thermal_array = get_thermal_data()
    
    # Save thermal image if available
    if thermal_array is not None:
        save_thermal_image(thermal_array)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    successful = sum(1 for r in results.values() if r["success"])
    print(f"   ✅ Successful endpoints: {successful}/{len(API_ENDPOINTS)}")
    print(f"   ❌ Failed endpoints: {len(API_ENDPOINTS) - successful}")
    
    # Show working endpoints
    print("\n🎉 Working endpoints:")
    for name, result in results.items():
        if result["success"]:
            print(f"   ✅ {name}")

if __name__ == "__main__":
    main()
