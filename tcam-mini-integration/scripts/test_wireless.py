#!/usr/bin/env python3
"""
Wireless Test Script for tCam-Mini
Tests completely wireless operation without USB cable
"""

import socket
import json
import subprocess
import time
import sys

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_usb_connection():
    """Check if tCam-Mini is connected via USB"""
    success, stdout, stderr = run_command("lsusb | grep -i 'espressif\\|silicon\\|cp210'")
    if success and stdout:
        print(f"⚠️  USB device detected: {stdout}")
        return True
    
    # Also check serial ports
    success, stdout, stderr = run_command("ls /dev/ttyUSB* 2>/dev/null")
    if success and stdout:
        print(f"⚠️  Serial port detected: {stdout}")
        return True
    
    print("✅ No USB connection detected")
    return False

def check_wifi_connection():
    """Check current WiFi connection"""
    success, stdout, stderr = run_command("nmcli -t -f active,ssid dev wifi | grep '^yes'")
    if success and stdout:
        ssid = stdout.split(':')[1] if ':' in stdout else stdout
        print(f"📡 Connected to WiFi: {ssid}")
        return ssid
    
    print("❌ No WiFi connection")
    return None

def test_tcam_connection(ip="192.168.4.1", port=5001):
    """Test socket connection to tCam-Mini"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((ip, port))
        
        # Send get_status command with correct protocol
        json_cmd = json.dumps({"cmd": "get_status"})
        message = b'\x02' + json_cmd.encode('utf-8') + b'\x03'
        sock.send(message)
        
        # Read response
        response = b''
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
            if b'\x03' in response:
                break
        
        sock.close()
        
        # Parse response
        if response.startswith(b'\x02') and b'\x03' in response:
            etx_pos = response.find(b'\x03')
            json_data = response[1:etx_pos].decode('utf-8')
            data = json.loads(json_data)
            
            if "status" in data:
                status = data["status"]
                print(f"✅ tCam-Mini connected wirelessly!")
                print(f"   Camera: {status.get('Camera', 'Unknown')}")
                print(f"   Version: {status.get('Version', 'Unknown')}")
                print(f"   Time: {status.get('Time', 'Unknown')}")
                return True
        
        print("❌ Invalid response from tCam-Mini")
        return False
        
    except Exception as e:
        print(f"❌ Cannot connect to tCam-Mini: {e}")
        return False

def disconnect_usb_advice():
    """Provide advice for disconnecting USB"""
    print("\n🔌 To test completely wireless operation:")
    print("1. Unplug the USB cable from tCam-Mini")
    print("2. Wait 5 seconds for the device to restart")
    print("3. Connect to tCam-Mini-CDE9 WiFi network")
    print("4. Run this test again")
    print("\n💡 The tCam-Mini should work purely on battery/external power")

def main():
    print("🔋 tCam-Mini Wireless Test")
    print("=" * 40)
    
    # Check USB connection
    usb_connected = check_usb_connection()
    
    # Check WiFi
    current_ssid = check_wifi_connection()
    
    # Test tCam connection
    if current_ssid == "tCam-Mini-CDE9":
        print("\n🎯 Testing tCam-Mini connection...")
        tcam_working = test_tcam_connection()
        
        if tcam_working and not usb_connected:
            print("\n🎉 SUCCESS: tCam-Mini is working completely wirelessly!")
            print("✅ No USB cable needed")
            print("✅ WiFi communication working")
            print("✅ Socket protocol working")
            print("\n🚀 You can now run the thermal viewer wirelessly!")
            
        elif tcam_working and usb_connected:
            print("\n⚠️  tCam-Mini is working but USB cable is still connected")
            disconnect_usb_advice()
            
        else:
            print("\n❌ tCam-Mini not responding")
            
    elif current_ssid:
        print(f"\n📡 Connected to {current_ssid} instead of tCam-Mini-CDE9")
        print("💡 Connect to tCam-Mini-CDE9 to test wireless operation")
        print("Command: nmcli device wifi connect 'tCam-Mini-CDE9'")
        
    else:
        print("\n❌ No WiFi connection")
        print("💡 Connect to tCam-Mini-CDE9 first")
    
    print("\n" + "=" * 40)

if __name__ == "__main__":
    main()
