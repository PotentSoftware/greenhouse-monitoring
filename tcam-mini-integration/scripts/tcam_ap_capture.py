#!/usr/bin/env python3
"""
tCam-Mini AP Mode Capture Script
Captures data from tCam-Mini and saves it for offline analysis
"""

import requests
import json
import time
from datetime import datetime
import os

# tCam-Mini AP mode configuration
TCAM_AP_IP = "192.168.4.1"
TIMEOUT = 5

# Output directory
OUTPUT_DIR = "/home/lio/github/greenhouse-monitoring/tcam-mini-integration/captures"

# API endpoints to test
API_ENDPOINTS = {
    "status": "/status",
    "config": "/config", 
    "thermal_raw": "/thermal_raw",
    "thermal_stats": "/thermal_stats",
    "info": "/info",
    "cmd": "/cmd"
}

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_endpoint(endpoint_name, endpoint_path, session_dir):
    """Capture data from a single endpoint"""
    url = f"http://{TCAM_AP_IP}{endpoint_path}"
    print(f"📡 Capturing {endpoint_name}: {url}")
    
    result = {
        "endpoint": endpoint_name,
        "path": endpoint_path,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "success": False
    }
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        result["status_code"] = response.status_code
        result["headers"] = dict(response.headers)
        
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                data = response.json()
                result["data"] = data
                result["data_type"] = "json"
                result["success"] = True
                print(f"   ✅ JSON data captured")
                
                # Save raw thermal data separately if it's large
                if endpoint_name == "thermal_raw" and "pixels" in data:
                    pixels_file = os.path.join(session_dir, "thermal_pixels.json")
                    with open(pixels_file, 'w') as f:
                        json.dump({"pixels": data["pixels"], "timestamp": result["timestamp"]}, f)
                    print(f"   💾 Thermal pixels saved separately")
                    
            except json.JSONDecodeError:
                # Save as binary if it's an image
                if 'image' in response.headers.get('content-type', ''):
                    image_file = os.path.join(session_dir, f"{endpoint_name}.jpg")
                    with open(image_file, 'wb') as f:
                        f.write(response.content)
                    result["data_type"] = "image"
                    result["data_file"] = image_file
                    result["data_size"] = len(response.content)
                    result["success"] = True
                    print(f"   ✅ Image saved ({len(response.content)} bytes)")
                else:
                    result["data"] = response.text
                    result["data_type"] = "text"
                    result["success"] = True
                    print(f"   ✅ Text data captured")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        result["error"] = f"Timeout after {TIMEOUT} seconds"
        print(f"   ❌ Timeout")
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused"
        print(f"   ❌ Connection refused")
    except Exception as e:
        result["error"] = str(e)
        print(f"   ❌ Error: {e}")
    
    return result

def capture_multiple_frames(session_dir, num_frames=5):
    """Capture multiple thermal frames"""
    print(f"\n📸 Capturing {num_frames} thermal frames...")
    frames = []
    
    for i in range(num_frames):
        print(f"   Frame {i+1}/{num_frames}...")
        try:
            response = requests.get(f"http://{TCAM_AP_IP}/thermal_raw", timeout=TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if "pixels" in data:
                    frames.append({
                        "frame": i+1,
                        "timestamp": datetime.now().isoformat(),
                        "pixels": data["pixels"]
                    })
                    print(f"      ✅ Captured")
                else:
                    print(f"      ❌ No pixel data")
            else:
                print(f"      ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        if i < num_frames - 1:
            time.sleep(1)  # Wait between frames
    
    # Save frames
    if frames:
        frames_file = os.path.join(session_dir, "thermal_frames.json")
        with open(frames_file, 'w') as f:
            json.dump(frames, f)
        print(f"   💾 Saved {len(frames)} frames")
    
    return frames

def main():
    print("🎯 tCam-Mini AP Mode Data Capture")
    print("=" * 50)
    print(f"📡 Target: {TCAM_AP_IP}")
    print(f"📁 Output: {OUTPUT_DIR}")
    print("=" * 50)
    
    # Create session directory
    ensure_output_dir()
    session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"session_{session_time}")
    os.makedirs(session_dir)
    print(f"\n📁 Session directory: {session_dir}")
    
    # Test connectivity
    print(f"\n🔗 Testing connectivity to {TCAM_AP_IP}...")
    try:
        response = requests.get(f"http://{TCAM_AP_IP}/", timeout=2)
        print("   ✅ tCam-Mini is reachable!")
    except:
        print("   ❌ Cannot reach tCam-Mini")
        print("\n⚠️  Please:")
        print("   1. Run: ./switch_wifi.sh tcam")
        print("   2. Wait for connection")
        print("   3. Run this script again")
        return
    
    # Capture all endpoints
    print("\n📡 Capturing API endpoints...")
    results = []
    for name, path in API_ENDPOINTS.items():
        result = capture_endpoint(name, path, session_dir)
        results.append(result)
        time.sleep(0.5)
    
    # Capture multiple thermal frames
    frames = capture_multiple_frames(session_dir)
    
    # Save summary
    summary = {
        "session_time": session_time,
        "tcam_ip": TCAM_AP_IP,
        "endpoints_tested": len(API_ENDPOINTS),
        "successful_endpoints": sum(1 for r in results if r["success"]),
        "thermal_frames_captured": len(frames),
        "results": results
    }
    
    summary_file = os.path.join(session_dir, "capture_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Capture Summary:")
    print(f"   ✅ Successful endpoints: {summary['successful_endpoints']}/{summary['endpoints_tested']}")
    print(f"   📸 Thermal frames: {summary['thermal_frames_captured']}")
    print(f"   📁 Data saved to: {session_dir}")
    print("\n🎉 Capture complete!")
    print("\n⚠️  You can now reconnect to your home network:")
    print("   Run: ./switch_wifi.sh home")

if __name__ == "__main__":
    main()
