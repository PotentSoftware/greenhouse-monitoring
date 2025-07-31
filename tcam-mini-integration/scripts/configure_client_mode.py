#!/usr/bin/env python3
"""
Configure tCam-Mini for WiFi Client Mode

This script connects to the tCam-Mini in AP mode and configures it to connect
to your home WiFi network instead. After configuration, the device will reboot
and connect to your home WiFi, allowing both your laptop and tCam-Mini to be
on the same network.
"""

import socket
import json
import time
import sys

# tCam-Mini configuration
TCAM_AP_IP = "192.168.4.1"
TCAM_PORT = 5001

# WiFi Client Configuration - MODIFY THESE VALUES
HOME_WIFI_SSID = "BT-X6F962"  # Your home WiFi SSID
HOME_WIFI_PASSWORD = "N7nCfV3RE6d4Ra"  # Your home WiFi password

# Network flags from net_utilities.h
NET_INFO_FLAG_STARTUP_ENABLE = 0x01
NET_INFO_FLAG_CLIENT_MODE = 0x80

def send_command(sock, command):
    """Send a JSON command and receive response"""
    message = json.dumps(command) + "\n"
    
    print(f"📤 Sending: {json.dumps(command, indent=2)}")
    sock.send(message.encode())
    
    # Receive response
    response = sock.recv(4096)
    if response:
        response_str = response.decode().strip()
        print(f"📥 Received: {response_str}")
        try:
            return json.loads(response_str)
        except json.JSONDecodeError:
            print("⚠️ Response is not valid JSON")
            return {"raw_response": response_str}
    return None

def get_current_wifi_config(sock):
    """Get current WiFi configuration"""
    print("\n🔍 Getting current WiFi configuration...")
    command = {"cmd": "get_wifi"}
    return send_command(sock, command)

def configure_client_mode(sock, ssid, password):
    """Configure tCam-Mini for client mode"""
    print(f"\n⚙️ Configuring client mode for SSID: {ssid}")
    
    # Calculate flags: Enable startup + Client mode
    flags = NET_INFO_FLAG_STARTUP_ENABLE | NET_INFO_FLAG_CLIENT_MODE
    
    command = {
        "cmd": "set_wifi",
        "sta_ssid": ssid,
        "sta_pw": password,
        "flags": flags
    }
    
    return send_command(sock, command)

def main():
    """Main configuration function"""
    print("🎯 tCam-Mini WiFi Client Mode Configuration")
    print("=" * 50)
    
    # Check if password is configured
    if HOME_WIFI_PASSWORD == "your_wifi_password_here":
        print("❌ ERROR: Please edit this script and set your WiFi password!")
        print("   Update the HOME_WIFI_PASSWORD variable at the top of the script.")
        sys.exit(1)
    
    print(f"📡 Target WiFi: {HOME_WIFI_SSID}")
    print(f"🎯 tCam-Mini AP: {TCAM_AP_IP}:{TCAM_PORT}")
    print("\n⚠️  IMPORTANT: Make sure you're connected to tCam-Mini AP network!")
    
    input("Press Enter to continue...")
    
    try:
        # Connect to tCam-Mini
        print(f"\n📡 Connecting to tCam-Mini at {TCAM_AP_IP}:{TCAM_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((TCAM_AP_IP, TCAM_PORT))
        print("✅ Connected to tCam-Mini!")
        
        # Get current configuration
        current_config = get_current_wifi_config(sock)
        if current_config:
            print("📋 Current configuration received")
        
        # Configure client mode
        result = configure_client_mode(sock, HOME_WIFI_SSID, HOME_WIFI_PASSWORD)
        
        if result and result.get("status") == "ok":
            print("\n✅ Configuration successful!")
            print("🔄 The tCam-Mini will now reboot and connect to your home WiFi.")
            print("📍 Look for it on your home network after reboot.")
            print("💡 You can now reconnect your laptop to home WiFi too.")
        else:
            print("\n❌ Configuration failed!")
            if result:
                print(f"Response: {result}")
        
        sock.close()
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused. Make sure:")
        print("   - tCam-Mini is powered on")
        print("   - You're connected to tCam-Mini AP network")
        print("   - Run: scripts/connect_tcam_simple.sh")
    except socket.timeout:
        print("❌ Connection timeout")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
