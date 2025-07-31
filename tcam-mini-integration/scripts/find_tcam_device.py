#!/usr/bin/env python3
"""
Find tCam-Mini device on network
Searches for the device by MAC address and tests connectivity
"""

import subprocess
import re
import socket
import json
import sys

# tCam-Mini MAC address (from your device)
TCAM_MAC = "34:86:5d:09:cd:e8"
TCAM_PORT = 5001

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return ""

def find_device_by_mac():
    """Find device IP by MAC address using ARP and nmap"""
    print(f"🔍 Searching for tCam-Mini (MAC: {TCAM_MAC})...")
    
    # First try ARP table
    print("Checking ARP table...")
    arp_output = run_command("arp -a")
    
    # Look for MAC address in ARP table
    for line in arp_output.split('\n'):
        if TCAM_MAC.lower() in line.lower():
            # Extract IP address
            ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
            if ip_match:
                ip = ip_match.group(1)
                print(f"✅ Found device in ARP table: {ip}")
                return ip
    
    print("Not found in ARP table, scanning network...")
    
    # Get network range
    ip_output = run_command("ip route | grep 'scope link' | head -1")
    if not ip_output:
        print("❌ Could not determine network range")
        return None
    
    # Extract network (e.g., 192.168.1.0/24)
    network_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', ip_output)
    if not network_match:
        print("❌ Could not parse network range")
        return None
    
    network = network_match.group(1)
    print(f"Scanning network: {network}")
    
    # Run nmap to discover devices
    nmap_output = run_command(f"nmap -sn {network}")
    
    # Run nmap with MAC detection
    print("Scanning for MAC addresses...")
    nmap_mac_output = run_command(f"sudo nmap -sn {network}")
    
    # Look for our MAC address
    lines = nmap_mac_output.split('\n')
    for i, line in enumerate(lines):
        if TCAM_MAC.lower() in line.lower():
            # Look for IP in previous lines
            for j in range(i-1, max(i-5, 0), -1):
                ip_match = re.search(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)', lines[j])
                if ip_match:
                    ip = ip_match.group(1)
                    print(f"✅ Found device via nmap: {ip}")
                    return ip
    
    print("❌ Device not found on network")
    return None

def test_tcam_connectivity(ip):
    """Test if we can connect to tCam-Mini socket service"""
    print(f"🔌 Testing connectivity to {ip}:{TCAM_PORT}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        result = sock.connect_ex((ip, TCAM_PORT))
        
        if result == 0:
            print(f"✅ Socket connection successful!")
            
            # Try to send a command
            try:
                cmd = {"command": "get_status"}
                cmd_json = json.dumps(cmd) + '\n'
                sock.send(cmd_json.encode())
                
                response = sock.recv(1024).decode()
                print(f"📡 Device response: {response[:100]}...")
                
                sock.close()
                return True
                
            except Exception as e:
                print(f"⚠️  Connected but communication failed: {e}")
                sock.close()
                return False
                
        else:
            print(f"❌ Connection failed (error {result})")
            sock.close()
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    print("tCam-Mini Device Finder")
    print("=" * 40)
    
    # Find device IP
    device_ip = find_device_by_mac()
    
    if not device_ip:
        print("\n💡 Device not found. Possible reasons:")
        print("  - Device is still in AP mode (not connected to home WiFi)")
        print("  - Device is not powered on")
        print("  - Device failed to connect to WiFi")
        print("  - Device is on a different network")
        print("\nTry:")
        print("  1. Check device serial output for connection status")
        print("  2. Verify WiFi credentials are correct")
        print("  3. Connect to tCam-Mini-CDE9 AP to check configuration")
        return
    
    # Test connectivity
    if test_tcam_connectivity(device_ip):
        print(f"\n🎉 tCam-Mini found and accessible at {device_ip}!")
        print(f"\nYou can now:")
        print(f"  • Run thermal viewer: python3 tcam_thermal_viewer.py --host {device_ip}")
        print(f"  • Access web interface: http://{device_ip}/")
        print(f"  • Test connection: python3 test_tcam_connection.py {device_ip}")
        
        # Update thermal viewer script with found IP
        try:
            with open('tcam_thermal_viewer.py', 'r') as f:
                content = f.read()
            
            # Update default host
            updated_content = re.sub(
                r"default='192\.168\.4\.1'",
                f"default='{device_ip}'",
                content
            )
            
            if updated_content != content:
                with open('tcam_thermal_viewer.py', 'w') as f:
                    f.write(updated_content)
                print(f"  • Updated tcam_thermal_viewer.py default host to {device_ip}")
                
        except Exception as e:
            print(f"  • Could not update thermal viewer script: {e}")
    
    else:
        print(f"\n⚠️  Device found at {device_ip} but not responding on port {TCAM_PORT}")
        print("  • Device may still be booting")
        print("  • Firmware may not be running correctly")
        print("  • Try connecting via web browser first")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific IP
        test_ip = sys.argv[1]
        print(f"Testing specific IP: {test_ip}")
        test_tcam_connectivity(test_ip)
    else:
        # Find device automatically
        main()
