#!/usr/bin/env python3
"""
Correct tCam-Mini Protocol Test
Uses proper delimiters: <0x02><json><0x03>
"""

import socket
import json
import time

def send_tcam_command(sock, command_dict):
    """Send command with correct tCam-Mini protocol"""
    try:
        # Create JSON command
        json_cmd = json.dumps(command_dict)
        
        # Wrap with STX (0x02) and ETX (0x03) delimiters
        full_cmd = b'\x02' + json_cmd.encode() + b'\x03'
        
        print(f"📤 Sending: {json_cmd}")
        print(f"📤 Bytes: {full_cmd.hex()}")
        
        # Send command
        sock.send(full_cmd)
        
        # Wait for response
        sock.settimeout(15)
        response = sock.recv(4096)
        
        print(f"📥 Raw response ({len(response)} bytes): {response.hex()}")
        
        # Parse response (should also have delimiters)
        if len(response) >= 2 and response[0] == 0x02:
            # Find ETX delimiter
            etx_pos = response.find(0x03)
            if etx_pos != -1:
                json_response = response[1:etx_pos].decode()
                print(f"📥 JSON: {json_response}")
                try:
                    return json.loads(json_response)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    return json_response
            else:
                print("❌ No ETX delimiter found")
                return response.decode()
        else:
            print(f"❌ No STX delimiter. Raw: {response}")
            return response
            
    except socket.timeout:
        print("❌ Socket timeout")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_correct_protocol():
    """Test tCam-Mini with correct protocol"""
    host = "192.168.4.1"
    port = 5001
    
    print(f"🔗 Testing CORRECT protocol to {host}:{port}")
    print("Protocol: <STX><JSON><ETX> where STX=0x02, ETX=0x03")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("✅ Connected!")
        
        # Test commands with correct protocol
        commands = [
            {"cmd": "get_status"},
            {"cmd": "get_config"},
            {"cmd": "get_wifi"},
            {"cmd": "get_image"},
        ]
        
        for cmd in commands:
            print(f"\n{'='*50}")
            print(f"Testing: {cmd}")
            response = send_tcam_command(sock, cmd)
            
            if response:
                print(f"✅ Got response!")
                if isinstance(response, dict):
                    for key, value in response.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  Response: {response}")
            else:
                print(f"❌ No response")
            
            time.sleep(2)  # Wait between commands
        
        sock.close()
        print("\n🔗 Socket closed")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    print("🎯 tCam-Mini CORRECT Protocol Test")
    print("=" * 50)
    test_correct_protocol()
