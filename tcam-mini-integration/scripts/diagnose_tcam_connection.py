#!/usr/bin/env python3
"""
Diagnose tCam-Mini Connection Issues

This script performs step-by-step diagnostics to identify why
the tCam-Mini socket connection is failing.
"""

import socket
import json
import time
import subprocess
import sys

TCAM_AP_IP = "192.168.4.1"
TCAM_PORT = 5001

def check_wifi_connection():
    """Check if connected to tCam-Mini AP"""
    print("🔍 Step 1: Checking WiFi connection...")
    
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    current_ssid = line.split(':', 1)[1]
                    print(f"📡 Currently connected to: {current_ssid}")
                    
                    if "tCam-Mini" in current_ssid:
                        print("✅ Connected to tCam-Mini AP")
                        return True
                    else:
                        print("❌ Not connected to tCam-Mini AP")
                        print("💡 Run: scripts/connect_tcam_simple.sh")
                        return False
    except Exception as e:
        print(f"❌ Error checking WiFi: {e}")
    
    return False

def check_network_connectivity():
    """Check basic network connectivity to tCam-Mini"""
    print(f"\n🔍 Step 2: Testing network connectivity to {TCAM_AP_IP}...")
    
    try:
        result = subprocess.run(['ping', '-c', '3', '-W', '3', TCAM_AP_IP], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ping successful - device is reachable")
            return True
        else:
            print("❌ Ping failed - device not reachable")
            print("💡 Device might be booting or network issue")
            return False
    except Exception as e:
        print(f"❌ Error pinging device: {e}")
        return False

def check_port_accessibility():
    """Check if port 5001 is accessible"""
    print(f"\n🔍 Step 3: Testing port {TCAM_PORT} accessibility...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((TCAM_AP_IP, TCAM_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {TCAM_PORT} is open and accessible")
            return True
        else:
            print(f"❌ Port {TCAM_PORT} is not accessible (error code: {result})")
            print("💡 Socket server might not be running")
            return False
    except Exception as e:
        print(f"❌ Error testing port: {e}")
        return False

def test_socket_communication():
    """Test actual socket communication"""
    print(f"\n🔍 Step 4: Testing socket communication...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        print(f"📡 Connecting to {TCAM_AP_IP}:{TCAM_PORT}...")
        sock.connect((TCAM_AP_IP, TCAM_PORT))
        print("✅ Socket connection established")
        
        # Try a simple command
        command = {"cmd": "get_status"}
        message = json.dumps(command) + "\n"
        
        print(f"📤 Sending command: {command}")
        sock.send(message.encode())
        
        print("📥 Waiting for response...")
        sock.settimeout(15)  # Longer timeout for response
        response = sock.recv(4096)
        
        if response:
            response_str = response.decode().strip()
            print(f"✅ Received response ({len(response_str)} bytes)")
            print(f"📋 Response: {response_str[:200]}{'...' if len(response_str) > 200 else ''}")
            
            try:
                json_response = json.loads(response_str)
                print("✅ Response is valid JSON")
                return True
            except json.JSONDecodeError:
                print("⚠️ Response is not valid JSON")
                return False
        else:
            print("❌ No response received")
            return False
            
    except socket.timeout:
        print("❌ Socket timeout - device not responding")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - socket server not running")
        return False
    except Exception as e:
        print(f"❌ Socket communication error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def check_serial_output():
    """Check if we can monitor serial output"""
    print(f"\n🔍 Step 5: Checking serial connection...")
    
    try:
        result = subprocess.run(['ls', '/dev/ttyUSB*'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            devices = result.stdout.strip().split('\n')
            print(f"📱 Found serial devices: {devices}")
            print("💡 You can monitor with: idf.py -p /dev/ttyUSB0 monitor")
            return True
        else:
            print("❌ No USB serial devices found")
            print("💡 Check USB connection to tCam-Mini")
            return False
    except Exception as e:
        print(f"❌ Error checking serial: {e}")
        return False

def main():
    """Run complete diagnostics"""
    print("🔧 tCam-Mini Connection Diagnostics")
    print("=" * 40)
    print()
    
    # Run all diagnostic steps
    steps_passed = 0
    total_steps = 5
    
    if check_wifi_connection():
        steps_passed += 1
    
    if check_network_connectivity():
        steps_passed += 1
    
    if check_port_accessibility():
        steps_passed += 1
    
    if test_socket_communication():
        steps_passed += 1
    
    if check_serial_output():
        steps_passed += 1
    
    print(f"\n📊 Diagnostic Summary")
    print("=" * 25)
    print(f"✅ Passed: {steps_passed}/{total_steps} steps")
    
    if steps_passed == total_steps:
        print("🎉 All diagnostics passed! Communication should work.")
    elif steps_passed >= 3:
        print("⚠️ Most steps passed. Issue might be intermittent.")
        print("💡 Try the configuration script again")
    else:
        print("❌ Multiple issues detected.")
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Power cycle the tCam-Mini device")
        print("2. Wait 30 seconds for full boot")
        print("3. Check USB connection and monitor serial output")
        print("4. Verify firmware was flashed correctly")

if __name__ == "__main__":
    main()
