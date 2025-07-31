#!/usr/bin/env python3
"""
Find tCam-Mini on Home Network

This script scans your home network to find the tCam-Mini device after it has
been configured for client mode. It uses multiple discovery methods:
1. mDNS discovery for _tcam-socket._tcp service
2. Network scanning for devices responding on port 5001
3. ARP table scanning for known MAC address patterns
"""

import socket
import json
import subprocess
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TCAM_PORT = 5001
SCAN_TIMEOUT = 2

def get_network_range():
    """Get the current network range for scanning"""
    try:
        # Get default route to determine network
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            # Extract interface
            interface = re.search(r'dev (\w+)', result.stdout)
            if interface:
                iface = interface.group(1)
                
                # Get IP and netmask for this interface
                result = subprocess.run(['ip', 'addr', 'show', iface], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    # Look for inet address
                    match = re.search(r'inet (\d+\.\d+\.\d+)\.\d+/(\d+)', result.stdout)
                    if match:
                        network_base = match.group(1)
                        prefix = int(match.group(2))
                        
                        if prefix == 24:  # /24 network
                            return f"{network_base}.0/24"
    except Exception as e:
        print(f"⚠️ Could not determine network range: {e}")
    
    # Default fallback
    return "192.168.1.0/24"

def scan_ip_for_tcam(ip):
    """Check if an IP address has tCam-Mini running on port 5001"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SCAN_TIMEOUT)
        result = sock.connect_ex((ip, TCAM_PORT))
        
        if result == 0:
            # Port is open, try to get status
            try:
                command = {"cmd": "get_status"}
                message = json.dumps(command) + "\n"
                sock.send(message.encode())
                
                response = sock.recv(1024)
                if response:
                    response_data = json.loads(response.decode())
                    if "status" in response_data:
                        sock.close()
                        return {
                            "ip": ip,
                            "port": TCAM_PORT,
                            "status": response_data,
                            "method": "port_scan"
                        }
            except:
                pass
            
            sock.close()
            return {
                "ip": ip,
                "port": TCAM_PORT,
                "status": "port_open",
                "method": "port_scan"
            }
        
        sock.close()
    except:
        pass
    
    return None

def network_scan():
    """Scan the local network for tCam-Mini devices"""
    print("🔍 Scanning local network for tCam-Mini devices...")
    
    network_range = get_network_range()
    print(f"📡 Scanning network: {network_range}")
    
    # Generate IP list for /24 network
    if "/24" in network_range:
        base = network_range.split("/")[0].rsplit(".", 1)[0]
        ip_list = [f"{base}.{i}" for i in range(1, 255)]
    else:
        # Fallback to common ranges
        ip_list = [f"192.168.1.{i}" for i in range(1, 255)]
        ip_list.extend([f"192.168.0.{i}" for i in range(1, 255)])
    
    found_devices = []
    
    # Use ThreadPoolExecutor for parallel scanning
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_ip = {executor.submit(scan_ip_for_tcam, ip): ip for ip in ip_list}
        
        for future in as_completed(future_to_ip):
            result = future.result()
            if result:
                found_devices.append(result)
                print(f"✅ Found tCam-Mini at {result['ip']}:{result['port']}")
    
    return found_devices

def mdns_discovery():
    """Try to discover tCam-Mini using mDNS"""
    print("🔍 Attempting mDNS discovery...")
    
    try:
        # Try using avahi-browse if available
        result = subprocess.run(['avahi-browse', '-t', '_tcam-socket._tcp', '-r'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Parse avahi-browse output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'address [' in line:
                    # Extract IP address
                    match = re.search(r'address \[([0-9.]+)\]', line)
                    if match:
                        ip = match.group(1)
                        print(f"✅ mDNS found tCam-Mini at {ip}")
                        return [{"ip": ip, "port": TCAM_PORT, "method": "mdns"}]
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ mDNS discovery not available or timed out")
    
    return []

def arp_scan():
    """Check ARP table for potential tCam-Mini devices"""
    print("🔍 Checking ARP table for ESP32 devices...")
    
    try:
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        if result.returncode == 0:
            # Look for ESP32-like MAC addresses (Espressif OUI: 34:86:5d, etc.)
            esp_ouis = ['34:86:5d', '24:6f:28', '30:ae:a4', 'a4:cf:12']
            
            devices = []
            for line in result.stdout.split('\n'):
                for oui in esp_ouis:
                    if oui in line.lower():
                        # Extract IP
                        match = re.search(r'\(([0-9.]+)\)', line)
                        if match:
                            ip = match.group(1)
                            devices.append({"ip": ip, "method": "arp", "mac_hint": oui})
                            print(f"💡 Found ESP32-like device at {ip} (MAC starts with {oui})")
            
            return devices
    except:
        pass
    
    return []

def test_tcam_connection(device_info):
    """Test if a discovered device is actually a tCam-Mini"""
    ip = device_info["ip"]
    print(f"\n🧪 Testing {ip}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, TCAM_PORT))
        
        # Try get_status command
        command = {"cmd": "get_status"}
        message = json.dumps(command) + "\n"
        sock.send(message.encode())
        
        response = sock.recv(1024)
        if response:
            response_data = json.loads(response.decode())
            sock.close()
            
            if "status" in response_data and response_data["status"] == "ok":
                print(f"✅ Confirmed tCam-Mini at {ip}")
                return True
        
        sock.close()
    except Exception as e:
        print(f"❌ Connection failed to {ip}: {e}")
    
    return False

def main():
    """Main discovery function"""
    print("🎯 tCam-Mini Network Discovery")
    print("=" * 40)
    print("Searching for tCam-Mini devices on your home network...")
    print()
    
    all_devices = []
    
    # Try multiple discovery methods
    mdns_devices = mdns_discovery()
    all_devices.extend(mdns_devices)
    
    arp_devices = arp_scan()
    all_devices.extend(arp_devices)
    
    # Network scan (this takes longer)
    scan_devices = network_scan()
    all_devices.extend(scan_devices)
    
    # Remove duplicates
    unique_ips = set()
    unique_devices = []
    for device in all_devices:
        if device["ip"] not in unique_ips:
            unique_ips.add(device["ip"])
            unique_devices.append(device)
    
    print(f"\n📊 Discovery Summary:")
    print(f"Found {len(unique_devices)} potential tCam-Mini device(s)")
    
    if unique_devices:
        print("\n🎯 Testing discovered devices...")
        confirmed_devices = []
        
        for device in unique_devices:
            if test_tcam_connection(device):
                confirmed_devices.append(device)
        
        if confirmed_devices:
            print(f"\n🎉 Found {len(confirmed_devices)} confirmed tCam-Mini device(s):")
            for device in confirmed_devices:
                print(f"   📍 {device['ip']}:{TCAM_PORT} (discovered via {device['method']})")
            
            print(f"\n💡 You can now test communication with:")
            for device in confirmed_devices:
                print(f"   python3 scripts/simple_tcam_test.py  # (edit IP to {device['ip']})")
        else:
            print("\n❌ No confirmed tCam-Mini devices found")
            print("💡 The device might still be rebooting or connecting to WiFi")
            print("   Try running this script again in a few minutes")
    else:
        print("\n❌ No potential devices found")
        print("💡 Make sure:")
        print("   - tCam-Mini has been configured for client mode")
        print("   - Device has had time to reboot and connect")
        print("   - Your laptop is on the same WiFi network")

if __name__ == "__main__":
    main()
