#!/usr/bin/env python3
"""
Wireless Connectivity Test for tCam-Mini
Tests full wireless operation after disconnecting USB
"""

import socket
import json
import time
import subprocess
import sys

def ping_device(ip, timeout=5):
    """Ping the device to check basic network connectivity"""
    try:
        result = subprocess.run(['ping', '-c', '3', '-W', str(timeout), ip], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def test_socket_connection(ip, port, timeout=5):
    """Test if socket port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def send_tcam_command(ip, port, command, timeout=10):
    """Send command to tCam and get response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        cmd_bytes = f'\x02{json.dumps(command)}\x03'.encode()
        sock.send(cmd_bytes)
        
        response = sock.recv(4096)
        sock.close()
        
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]
        
        return json.loads(response.decode('utf-8'))
    except Exception as e:
        return None

def comprehensive_wireless_test(ip="192.168.1.130", port=5001):
    """Run comprehensive wireless connectivity test"""
    
    print("🔋 tCam-Mini Wireless Operation Test")
    print("=" * 50)
    print("📋 INSTRUCTIONS:")
    print("   1. Disconnect USB cable from tCam-Mini")
    print("   2. Connect external 5V power supply")
    print("   3. Wait 30-60 seconds for device to boot")
    print("   4. Press ENTER when ready to test...")
    print()
    
    input("⏳ Press ENTER when tCam-Mini is powered wirelessly...")
    print()
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Network Ping
    print("🔍 Test 1: Network Ping")
    print("-" * 25)
    if ping_device(ip):
        print(f"✅ Device responds to ping at {ip}")
        tests_passed += 1
    else:
        print(f"❌ Device does not respond to ping at {ip}")
    print()
    
    # Test 2: Socket Port Accessibility
    print("🔍 Test 2: Socket Port Access")
    print("-" * 30)
    if test_socket_connection(ip, port):
        print(f"✅ Socket port {port} is accessible")
        tests_passed += 1
    else:
        print(f"❌ Socket port {port} is not accessible")
    print()
    
    # Test 3: Device Status Command
    print("🔍 Test 3: Device Status")
    print("-" * 25)
    status = send_tcam_command(ip, port, {"cmd": "get_status"})
    if status and "status" in status:
        print(f"✅ Device status: {status['status']['Camera']} v{status['status']['Version']}")
        tests_passed += 1
    else:
        print("❌ Failed to get device status")
    print()
    
    # Test 4: Configuration Access
    print("🔍 Test 4: Configuration Access")
    print("-" * 32)
    config = send_tcam_command(ip, port, {"cmd": "get_config"})
    if config and "config" in config:
        print(f"✅ Device config accessible")
        print(f"   AGC: {'Enabled' if config['config']['agc_enabled'] else 'Disabled'}")
        print(f"   Emissivity: {config['config']['emissivity']}")
        tests_passed += 1
    else:
        print("❌ Failed to get device configuration")
    print()
    
    # Test 5: Thermal Image Capture
    print("🔍 Test 5: Thermal Image Capture")
    print("-" * 33)
    image_data = send_tcam_command(ip, port, {"cmd": "get_image"}, timeout=15)
    if image_data and "radiometric" in image_data:
        print("✅ Thermal image data captured successfully")
        print(f"   Data size: {len(image_data['radiometric'])} characters")
        tests_passed += 1
    else:
        print("❌ Failed to capture thermal image")
    print()
    
    # Results Summary
    print("📊 WIRELESS TEST RESULTS")
    print("=" * 30)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 SUCCESS: tCam-Mini is fully operational wirelessly!")
        print("✅ Station mode configuration is working perfectly")
        print("🌐 Device is ready for deployment without USB connection")
        return True
    elif tests_passed >= 3:
        print("⚠️  PARTIAL SUCCESS: Most functions working wirelessly")
        print("🔧 Some features may need troubleshooting")
        return True
    else:
        print("❌ FAILURE: Wireless operation not working properly")
        print("🔍 Check power supply and WiFi configuration")
        return False

def quick_connectivity_check(ip="192.168.1.130", port=5001):
    """Quick check if device is accessible"""
    print(f"🔍 Quick connectivity check to {ip}:{port}")
    
    if ping_device(ip, 3):
        print("✅ Device responds to ping")
        
        if test_socket_connection(ip, port, 3):
            print("✅ Socket port accessible")
            
            status = send_tcam_command(ip, port, {"cmd": "get_status"}, 5)
            if status:
                print("✅ Device responding to commands")
                return True
            else:
                print("❌ Device not responding to commands")
        else:
            print("❌ Socket port not accessible")
    else:
        print("❌ Device not responding to ping")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_connectivity_check()
    else:
        comprehensive_wireless_test()
