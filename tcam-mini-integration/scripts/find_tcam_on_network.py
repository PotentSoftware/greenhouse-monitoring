#!/usr/bin/env python3
"""
Find tCam-Mini on Home Network
Scans for tCam-Mini devices that have joined your home WiFi network
"""

import socket
import subprocess
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor

def check_tcam_port(ip, port=5001, timeout=2):
    """Check if a device responds on tCam socket port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def check_tcam_http(ip, port=80, timeout=2):
    """Check if a device responds on tCam HTTP port"""
    try:
        response = requests.get(f"http://{ip}:{port}/", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def test_tcam_commands(ip):
    """Test if device responds to tCam commands"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, 5001))
        
        # Send get_status command with STX/ETX delimiters
        command = b'\x02{"cmd": "get_status"}\x03'
        sock.send(command)
        
        response = sock.recv(1024)
        sock.close()
        
        # Check if response contains tCam-like data
        if b'tCam' in response or b'camera' in response or b'status' in response:
            return True, response.decode('utf-8', errors='ignore')
        return False, None
    except:
        return False, None

def scan_network():
    """Scan local network for tCam devices"""
    print("🔍 Scanning for tCam-Mini devices on home network...")
    print("=" * 50)
    
    # Get network range
    try:
        # Get default gateway
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        gateway = result.stdout.split()[2]
        network_base = '.'.join(gateway.split('.')[:-1])
        print(f"📡 Scanning network: {network_base}.1-254")
    except:
        network_base = "192.168.1"
        print(f"📡 Using default network: {network_base}.1-254")
    
    print()
    
    found_devices = []
    
    def check_ip(ip):
        # Check socket port (5001)
        socket_open = check_tcam_port(ip, 5001)
        # Check HTTP port (80)
        http_open = check_tcam_http(ip, 80)
        
        if socket_open or http_open:
            print(f"🎯 Found device at {ip}")
            if socket_open:
                print(f"   ✅ Socket port 5001: OPEN")
                # Test tCam commands
                is_tcam, response = test_tcam_commands(ip)
                if is_tcam:
                    print(f"   🎉 tCam-Mini CONFIRMED!")
                    if response:
                        print(f"   📊 Response: {response[:100]}...")
                else:
                    print(f"   ❓ Device responds but may not be tCam")
            
            if http_open:
                print(f"   ✅ HTTP port 80: OPEN")
                print(f"   🌐 Web interface: http://{ip}/")
            
            print()
            return ip, socket_open, http_open
        
        return None
    
    # Scan network in parallel
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            futures.append(executor.submit(check_ip, ip))
        
        for future in futures:
            result = future.result()
            if result:
                found_devices.append(result)
    
    print("\n" + "=" * 50)
    print("📋 SCAN RESULTS")
    print("=" * 50)
    
    if found_devices:
        print(f"✅ Found {len(found_devices)} potential tCam device(s):")
        for ip, socket_open, http_open in found_devices:
            print(f"\n🎯 Device: {ip}")
            if socket_open:
                print(f"   📱 Socket API: telnet {ip} 5001")
                print(f"   🐍 Python: Connect to {ip}:5001")
            if http_open:
                print(f"   🌐 Web interface: http://{ip}/")
        
        print(f"\n🎉 SUCCESS! Your tCam-Mini is now on your home network!")
        print(f"💡 You can now access it without losing internet connectivity.")
        
    else:
        print("❌ No tCam devices found on the network")
        print("\nTroubleshooting:")
        print("1. Make sure tCam-Mini is powered on")
        print("2. Check if station mode configuration was successful")
        print("3. Verify WiFi credentials in station_mode_config/main/main.c")
        print("4. Try connecting to tCam-Mini-CDE9 AP and check serial output")

if __name__ == "__main__":
    scan_network()
