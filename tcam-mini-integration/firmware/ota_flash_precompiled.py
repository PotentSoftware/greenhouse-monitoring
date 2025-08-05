#!/usr/bin/env python3
"""
OTA Flash Precompiled tCam-Mini Firmware

This script uploads the precompiled firmware binary to tCam-Mini via OTA.
The precompiled firmware should have working thermal sensor and socket commands.
"""

import requests
import sys
import os
import time
import json
import subprocess
import re

def find_tcam_device():
    """Find the real tCam-Mini device on network"""
    print("🔍 Scanning network for tCam-Mini device...")
    
    # First check if tCam-Mini is in AP mode
    print("\n🔍 Checking for AP mode...")
    try:
        # Check if we can connect to AP mode
        result = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], 
                              capture_output=True, text=True)
        if 'tCam-Mini-CDE9' in result.stdout:
            print("✅ Found tCam-Mini in AP mode")
            print("⚠️  Need to connect to AP mode first for OTA update")
            return "http://192.168.4.1"
    except:
        pass
    
    # Scan home network for devices
    try:
        result = subprocess.run(['nmap', '-sn', '192.168.1.0/24'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            # Look for IPs in the output
            ips = re.findall(r'192\.168\.1\.\d+', result.stdout)
            print(f"Found {len(ips)} devices on network")
            
            # Test each IP for tCam-Mini characteristics
            for ip in ips:
                if ip == "192.168.1.223":  # Skip our own IP
                    continue
                    
                # Test for OTA endpoint
                for port in [80, 5001, 8080]:
                    try:
                        url = f"http://{ip}:{port}"
                        print(f"Testing {url}...")
                        
                        # Test for OTA endpoint specifically
                        response = requests.post(f"{url}/ota", 
                                               data=b"test", 
                                               headers={'Content-Type': 'application/octet-stream'},
                                               timeout=3)
                        
                        # If we get any response (even error), it might be tCam
                        if response.status_code in [200, 400, 413, 500]:
                            # Avoid known services
                            if 'grafana' in response.text.lower():
                                print(f"  ❌ Grafana detected at {url} - skipping")
                                continue
                            if 'apache' in response.text.lower():
                                print(f"  ❌ Apache server detected at {url} - skipping")
                                continue
                                
                            print(f"  ✅ Found potential tCam-Mini at {url}")
                            return url
                            
                    except requests.exceptions.RequestException:
                        continue
                        
    except subprocess.TimeoutExpired:
        print("Network scan timed out")
    except Exception as e:
        print(f"Network scan failed: {e}")
    
    return None

def upload_firmware(base_url, firmware_path):
    """Upload precompiled firmware to tCam-Mini device"""
    if not os.path.exists(firmware_path):
        print(f"Error: Firmware file not found: {firmware_path}")
        return False
    
    file_size = os.path.getsize(firmware_path)
    print(f"Uploading precompiled firmware from {firmware_path}")
    print(f"Firmware size: {file_size:,} bytes")
    
    with open(firmware_path, 'rb') as f:
        firmware_data = f.read()
    
    try:
        print(f"Uploading to {base_url}/ota...")
        response = requests.post(
            f"{base_url}/ota",
            data=firmware_data,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=120  # Longer timeout for larger upload
        )
        
        if response.status_code == 200:
            print(f"✅ Success! Precompiled firmware uploaded")
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    firmware_path = "/home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware/tcam-firmware/precompiled/tCamMini.bin"
    
    print("🔥 tCam-Mini Precompiled Firmware OTA Upload")
    print("=" * 50)
    print("📦 Using precompiled firmware (should have working thermal sensor)")
    
    # Find the device
    device_url = find_tcam_device()
    if not device_url:
        print("❌ Error: Could not find tCam-Mini device on network")
        print("\n🔧 Troubleshooting:")
        print("1. If device is in AP mode:")
        print("   nmcli device wifi connect 'tCam-Mini-CDE9'")
        print("   python3 ota_flash_precompiled.py")
        print("2. Ensure device is powered on and connected to network")
        print("3. Check device IP address")
        return 1
    
    # Upload firmware
    if upload_firmware(device_url, firmware_path):
        print("\n🎉 Precompiled firmware upload completed successfully!")
        print("📱 The device should reboot automatically with working firmware.")
        print("🌡️  This firmware should have:")
        print("   ✅ Working Lepton thermal sensor")
        print("   ✅ Functional socket commands")
        print("   ✅ Proper thermal data streaming")
        return 0
    else:
        print("\n❌ Precompiled firmware upload failed!")
        print("💡 You may need to:")
        print("   1. Connect via USB and flash manually")
        print("   2. Use the official tCam Desktop Application")
        return 1

if __name__ == "__main__":
    sys.exit(main())
