#!/usr/bin/env python3
"""
tCam-Mini Socket Communication Test

The tCam-Mini uses TCP socket communication with JSON messages
when in client mode (connected to home WiFi).
"""

import socket
import json
import time
import sys

# tCam-Mini IP addresses to test
TCAM_IPS = [
    "192.168.4.1",   # Default AP mode IP (current)
    "192.168.1.246",  # Static IP on home network
    "192.168.1.138",  # DHCP IP discovered earlier
]
TCAM_PORT = 5001  # tCam-Mini command port from system_config.h

def test_socket_communication():
    """Test socket-based communication with tCam-Mini"""
    for TCAM_IP in TCAM_IPS:
        print(f"🔍 Testing socket communication with tCam-Mini at {TCAM_IP}:{TCAM_PORT}")
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            print(f"📡 Connecting to {TCAM_IP}:{TCAM_PORT}...")
            sock.connect((TCAM_IP, TCAM_PORT))
            print("✅ Socket connection established!")
            
            # Try to send a simple command
            command = {"cmd": "get_status"}
            message = json.dumps(command) + "\n"
            
            print(f"📤 Sending command: {command}")
            sock.send(message.encode())
            
            # Try to receive response
            print("📥 Waiting for response...")
            response = sock.recv(1024)
            
            if response:
                print(f"✅ Received response: {response.decode()}")
                try:
                    json_response = json.loads(response.decode())
                    print(f"📋 Parsed JSON: {json.dumps(json_response, indent=2)}")
                except json.JSONDecodeError:
                    print("⚠️ Response is not valid JSON")
            else:
                print("❌ No response received")
                
            sock.close()
            return True  # Success, stop trying other IPs
            
        except ConnectionRefusedError:
            print(f"❌ Connection refused on port {TCAM_PORT}")
        except socket.timeout:
            print(f"❌ Connection timeout on port {TCAM_PORT}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False  # No successful connection

def scan_common_ports():
    """Scan common ports that tCam-Mini might use"""
    common_ports = [23, 80, 8080, 443, 8443, 5000, 5001, 8000, 8888, 9999]
    
    for TCAM_IP in TCAM_IPS:
        print(f"🔍 Scanning common ports on {TCAM_IP}...")
        
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((TCAM_IP, port))
                
                if result == 0:
                    print(f"✅ Port {port} is open")
                else:
                    print(f"❌ Port {port} is closed")
                    
                sock.close()
                
            except Exception as e:
                print(f"❌ Error testing port {port}: {e}")
        print()  # Empty line between IPs

if __name__ == "__main__":
    print("🎯 tCam-Mini Socket Communication Test")
    print("=" * 50)
    
    # First scan for open ports
    scan_common_ports()
    
    print("\n" + "=" * 50)
    
    # Then try socket communication
    test_socket_communication()
    
    print("\n🎉 Socket testing complete!")
