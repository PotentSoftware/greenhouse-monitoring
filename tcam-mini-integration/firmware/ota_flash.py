#!/usr/bin/env python3
"""
tCam-Mini OTA Firmware Upload Script

This script attempts to upload firmware to a tCam-Mini device over WiFi
using the device's built-in OTA update mechanism.
"""

import requests
import sys
import os
import time
import json

def find_tcam_device():
    """Try to find tCam-Mini device on network"""
    print("🔍 Scanning network for tCam-Mini device...")
    
    # First try to find device using network scan
    import subprocess
    import re
    
    # Scan local network for devices
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
                    
                # Test common tCam ports
                for port in [5001, 8080, 80]:
                    try:
                        url = f"http://{ip}:{port}"
                        print(f"Testing {url}...")
                        response = requests.get(f"{url}/status", timeout=3)
                        
                        if response.status_code == 200:
                            # Avoid Grafana (port 3000) and other services
                            if port == 3000 and 'grafana' in response.text.lower():
                                print(f"  ❌ Grafana detected at {url} - skipping")
                                continue
                            if 'apache' in response.text.lower():
                                print(f"  ❌ Apache server detected at {url} - skipping")
                                continue
                                
                            # Look for tCam characteristics
                            if ('device' in response.text.lower() or 
                                'tcam' in response.text.lower() or
                                'thermal' in response.text.lower() or
                                'lepton' in response.text.lower()):
                                print(f"  ✅ Found tCam-Mini at {url}")
                                return url
                            else:
                                print(f"  ⚠️  HTTP server at {url} but not tCam")
                                
                    except requests.exceptions.RequestException:
                        continue
                        
        # Also try socket connection test for port 5001
        for ip in ips:
            if ip == "192.168.1.223":  # Skip our own IP
                continue
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, 5001))
                sock.close()
                if result == 0:
                    print(f"  ✅ Found socket server at {ip}:5001 (likely tCam-Mini)")
                    return f"http://{ip}:5001"
            except:
                continue
                
    except subprocess.TimeoutExpired:
        print("Network scan timed out")
    except Exception as e:
        print(f"Network scan failed: {e}")
    
    # Fallback to AP mode
    print("\n🔍 Checking for AP mode...")
    try:
        response = requests.get("http://192.168.4.1/status", timeout=3)
        if response.status_code == 200:
            print("✅ Found tCam-Mini in AP mode at 192.168.4.1")
            return "http://192.168.4.1"
    except:
        pass
    
    return None

def upload_firmware(base_url, firmware_path):
    """Upload firmware to tCam-Mini device"""
    if not os.path.exists(firmware_path):
        print(f"Error: Firmware file not found: {firmware_path}")
        return False
    
    print(f"Uploading firmware from {firmware_path} to {base_url}")
    
    # Try different possible OTA endpoints
    ota_endpoints = [
        "/ota",
        "/update", 
        "/firmware",
        "/upload"
    ]
    
    with open(firmware_path, 'rb') as f:
        firmware_data = f.read()
    
    for endpoint in ota_endpoints:
        try:
            print(f"Trying endpoint {endpoint}...")
            url = f"{base_url}{endpoint}"
            
            # Try POST with binary data
            response = requests.post(
                url,
                data=firmware_data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"Success! Firmware uploaded via {endpoint}")
                return True
            else:
                print(f"Failed at {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Error at {endpoint}: {e}")
    
    return False

def main():
    firmware_path = "/home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware/tcam-firmware/build/tCamMini.bin"
    
    print("tCam-Mini OTA Firmware Upload")
    print("=" * 40)
    
    # Find the device
    device_url = find_tcam_device()
    if not device_url:
        print("Error: Could not find tCam-Mini device on network")
        print("\nTroubleshooting:")
        print("1. Ensure tCam-Mini is powered on and connected to WiFi")
        print("2. Check if device is in AP mode (connect to tCam-Mini-XXXX WiFi)")
        print("3. Verify the IP address is correct")
        return 1
    
    # Upload firmware
    if upload_firmware(device_url, firmware_path):
        print("\nFirmware upload completed successfully!")
        print("The device should reboot automatically with the new firmware.")
        return 0
    else:
        print("\nFirmware upload failed!")
        print("You may need to use the official tCam Desktop Application for OTA updates.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
