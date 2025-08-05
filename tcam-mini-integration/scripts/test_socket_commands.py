#!/usr/bin/env python3
"""
Test tCam-Mini Socket Commands
Direct socket communication with tCam-Mini to get thermal data
"""

import socket
import json
import time
import sys

def send_command(sock, command):
    """Send a JSON command to tCam-Mini socket"""
    try:
        cmd_str = json.dumps(command) + '\n'
        print(f"📤 Sending: {cmd_str.strip()}")
        sock.send(cmd_str.encode())
        
        # Wait for response
        sock.settimeout(10)
        response = sock.recv(4096).decode().strip()
        print(f"📥 Received: {response[:200]}...")
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"⚠️  Non-JSON response: {response}")
            return response
            
    except socket.timeout:
        print("❌ Socket timeout waiting for response")
        return None
    except Exception as e:
        print(f"❌ Socket error: {e}")
        return None

def test_tcam_socket():
    """Test tCam-Mini socket communication"""
    host = "192.168.4.1"
    port = 5001
    
    print(f"🔗 Connecting to tCam-Mini at {host}:{port}")
    
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        print("✅ Socket connected!")
        
        # Test commands
        commands = [
            {"cmd": "get_status"},
            {"cmd": "get_wifi"},
            {"cmd": "get_config"},
            {"cmd": "get_image"},
            {"cmd": "get_thermal"},
            {"cmd": "stream_on"},
            {"cmd": "get_lep_cci"},
            {"cmd": "get_fw_info"}
        ]
        
        for cmd in commands:
            print(f"\n{'='*50}")
            response = send_command(sock, cmd)
            if response:
                if isinstance(response, dict):
                    print(f"✅ Command '{cmd['cmd']}' successful")
                    for key, value in response.items():
                        if key == 'thermal_pixels' and isinstance(value, list):
                            print(f"  {key}: [array of {len(value)} pixels]")
                        else:
                            print(f"  {key}: {value}")
                else:
                    print(f"✅ Command '{cmd['cmd']}' returned: {response}")
            else:
                print(f"❌ Command '{cmd['cmd']}' failed")
            
            time.sleep(1)  # Brief pause between commands
        
        sock.close()
        print("\n🔗 Socket closed")
        
    except ConnectionRefusedError:
        print("❌ Connection refused - socket server not running")
    except socket.timeout:
        print("❌ Connection timeout")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🌡️ tCam-Mini Socket Command Tester")
    print("=" * 50)
    test_tcam_socket()
