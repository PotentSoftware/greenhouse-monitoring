#!/usr/bin/env python3
"""
Simple tCam-Mini socket test - direct connection to port 5001
"""

import socket
import json
import time

TCAM_IP = "192.168.4.1"
TCAM_PORT = 5001

def test_tcam_connection():
    """Test direct connection to tCam-Mini on port 5001"""
    print(f"🎯 Testing tCam-Mini at {TCAM_IP}:{TCAM_PORT}")
    
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
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
        return True
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused on port {TCAM_PORT}")
        return False
    except socket.timeout:
        print(f"❌ Connection timeout on port {TCAM_PORT}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Simple tCam-Mini Socket Test")
    print("=" * 40)
    
    success = test_tcam_connection()
    
    if success:
        print("\n🎉 Connection test successful!")
    else:
        print("\n❌ Connection test failed!")
        print("💡 Make sure:")
        print("   - tCam-Mini is powered on")
        print("   - Connected to tCam-Mini AP network")
        print("   - Firmware is running with socket server")
