#!/usr/bin/env python3
"""
tCam-Mini Network Diagnostic
Comprehensive network troubleshooting for tCam-Mini
"""

import socket
import subprocess
import json
import time

def check_wifi_networks():
    """Check for tCam-Mini AP mode"""
    try:
        result = subprocess.run(['nmcli', 'dev', 'wifi', 'list'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            tcam_networks = [line for line in lines if 'tCam-Mini' in line]
            return tcam_networks
        return []
    except:
        return []

def test_ip_and_ports(ip):
    """Test various ports on an IP"""
    ports_to_test = [80, 5001, 8080, 23, 22]
    results = {}
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip, port))
            sock.close()
            results[port] = (result == 0)
        except:
            results[port] = False
    
    return results

def test_tcam_command(ip, port=5001):
    """Test tCam command response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        
        command = b'\x02{"cmd": "get_status"}\x03'
        sock.send(command)
        response = sock.recv(1024)
        sock.close()
        
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]
            data = json.loads(response.decode('utf-8'))
            return data
        return None
    except Exception as e:
        return f"Error: {e}"

def comprehensive_diagnostic():
    """Run comprehensive tCam-Mini network diagnostic"""
    
    print("🔍 tCam-Mini Network Diagnostic")
    print("=" * 50)
    
    # 1. Check for AP mode
    print("\n1. 📡 Checking for tCam-Mini AP mode...")
    wifi_networks = check_wifi_networks()
    if wifi_networks:
        print("✅ Found tCam-Mini AP networks:")
        for network in wifi_networks:
            print(f"   {network}")
        print("⚠️  Device may have reverted to AP mode!")
    else:
        print("❌ No tCam-Mini AP networks found")
    
    # 2. Test known IPs
    print("\n2. 🌐 Testing known IP addresses...")
    test_ips = ["192.168.1.130", "192.168.1.138", "192.168.4.1"]
    
    for ip in test_ips:
        print(f"\n   Testing {ip}:")
        
        # Ping test
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], 
                                  capture_output=True, text=True)
            ping_ok = result.returncode == 0
            print(f"   📍 Ping: {'✅ OK' if ping_ok else '❌ Failed'}")
        except:
            ping_ok = False
            print("   📍 Ping: ❌ Failed")
        
        if ping_ok:
            # Port tests
            port_results = test_ip_and_ports(ip)
            for port, is_open in port_results.items():
                status = "✅ Open" if is_open else "❌ Closed"
                print(f"   🔌 Port {port}: {status}")
            
            # tCam command test
            if port_results.get(5001, False):
                print("   🎯 Testing tCam commands...")
                cmd_result = test_tcam_command(ip)
                if isinstance(cmd_result, dict):
                    print(f"   ✅ tCam responding: {cmd_result.get('status', {}).get('Camera', 'Unknown')}")
                else:
                    print(f"   ❌ tCam command failed: {cmd_result}")
    
    # 3. Network scan for new IPs
    print("\n3. 🔍 Scanning for tCam-Mini on network...")
    print("   (This may take a moment...)")
    
    # Quick scan of common range
    base_ip = "192.168.1."
    found_devices = []
    
    for i in range(100, 200):  # Scan common DHCP range
        ip = f"{base_ip}{i}"
        try:
            # Quick ping
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Check if port 5001 is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((ip, 5001)) == 0:
                    sock.close()
                    # Test if it's a tCam
                    cmd_result = test_tcam_command(ip)
                    if isinstance(cmd_result, dict):
                        found_devices.append((ip, cmd_result))
                else:
                    sock.close()
        except:
            pass
    
    if found_devices:
        print("\n✅ Found tCam-Mini devices:")
        for ip, info in found_devices:
            camera_name = info.get('status', {}).get('Camera', 'Unknown')
            version = info.get('status', {}).get('Version', 'Unknown')
            print(f"   🎯 {ip}: {camera_name} v{version}")
    else:
        print("\n❌ No tCam-Mini devices found on network")
    
    # 4. Recommendations
    print("\n4. 💡 Recommendations:")
    if wifi_networks:
        print("   • Device appears to be in AP mode")
        print("   • Try connecting to tCam-Mini-XXXX network")
        print("   • Re-flash station mode firmware if needed")
    elif not found_devices:
        print("   • Power cycle the tCam-Mini device")
        print("   • Check power supply connection")
        print("   • Verify WiFi credentials in firmware")
        print("   • Consider re-flashing station mode firmware")
    else:
        print("   • Update scripts with new IP address")
        print("   • Test thermal image capture")

if __name__ == "__main__":
    comprehensive_diagnostic()
