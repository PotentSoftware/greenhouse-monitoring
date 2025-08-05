#!/usr/bin/env python3
"""
Debug tCam-Mini Commands
Test different commands to see what the device responds to
"""

import socket
import json
import time

def send_tcam_command(ip, port, command, timeout=5):
    """Send a command to tCam-Mini and return response"""
    try:
        print(f"📤 Sending: {command}")
        
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        # Send command with STX/ETX delimiters
        cmd_bytes = f'\x02{json.dumps(command)}\x03'.encode()
        sock.send(cmd_bytes)
        
        # Receive response
        response = sock.recv(4096)
        sock.close()
        
        # Strip delimiters
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]
        
        response_str = response.decode('utf-8', errors='ignore')
        print(f"📥 Response: {response_str}")
        
        try:
            return json.loads(response_str)
        except:
            return response_str
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_tcam_commands(ip="192.168.1.138", port=5001):
    """Test various tCam commands"""
    print(f"🎯 Testing tCam-Mini Commands at {ip}:{port}")
    print("=" * 50)
    
    # List of commands to test
    commands = [
        {"cmd": "get_status"},
        {"cmd": "get_image"},
        {"cmd": "get_config"},
        {"cmd": "stream_on"},
        {"cmd": "stream_off"},
        {"cmd": "get_lep_cci"},
        {"cmd": "set_time", "sec": int(time.time())},
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n{i}. Testing command: {command['cmd']}")
        print("-" * 30)
        
        response = send_tcam_command(ip, port, command)
        
        if response:
            print(f"✅ Success!")
            if isinstance(response, dict):
                for key, value in response.items():
                    if key == "image" and isinstance(value, dict):
                        # Don't print huge image data
                        print(f"   {key}: {list(value.keys())} (image data)")
                    else:
                        print(f"   {key}: {value}")
        else:
            print(f"❌ Failed or no response")
        
        time.sleep(1)  # Brief pause between commands

if __name__ == "__main__":
    test_tcam_commands()
