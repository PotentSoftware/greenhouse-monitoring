#!/usr/bin/env python3
"""
Scan network for tCam-Mini device on port 5001
"""

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def test_ip(ip):
    """Test if a specific IP responds on port 5001"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 5001))
        sock.close()
        if result == 0:
            return ip
    except:
        pass
    return None

def scan_network(base_ip="192.168.1"):
    """Scan network range for tCam-Mini"""
    print(f"🔍 Scanning {base_ip}.1-254 for tCam-Mini on port 5001...")
    print("This may take a moment...")
    
    found_devices = []
    
    # Use ThreadPoolExecutor for faster scanning
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            futures.append(executor.submit(test_ip, ip))
        
        for future in futures:
            result = future.result()
            if result:
                found_devices.append(result)
                print(f"✅ Found device at {result}:5001")
    
    return found_devices

if __name__ == "__main__":
    print("tCam-Mini Network Scanner")
    print("=" * 40)
    
    # Scan common network ranges
    networks = ["192.168.1", "192.168.0", "10.0.0"]
    
    all_devices = []
    for network in networks:
        devices = scan_network(network)
        all_devices.extend(devices)
        if devices:
            break  # Stop after finding devices in first network
    
    print("\n" + "=" * 40)
    if all_devices:
        print(f"🎉 Found {len(all_devices)} tCam device(s):")
        for device in all_devices:
            print(f"   📍 {device}:5001")
        
        # Test the first device found
        if all_devices:
            print(f"\n🧪 Testing connection to {all_devices[0]}...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((all_devices[0], 5001))
                print("✅ Socket connection successful!")
                sock.close()
            except Exception as e:
                print(f"❌ Socket test failed: {e}")
    else:
        print("❌ No tCam devices found on scanned networks")
        print("\n💡 Troubleshooting:")
        print("1. Check if device is powered on")
        print("2. Verify WiFi credentials are correct")
        print("3. Check serial monitor for connection status")
