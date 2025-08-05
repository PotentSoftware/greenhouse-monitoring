#!/usr/bin/env python3
"""
Test tCam-Mini in Station Mode
Quick test to verify tCam-Mini is working on home network
"""

import socket
import json
import sys

def test_tcam_command(ip, port=5001):
    """Test tCam-Mini with get_status command"""
    try:
        print(f"🔍 Testing tCam-Mini at {ip}:{port}")
        
        # Connect to tCam
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, port))
        print(f"✅ Connected to {ip}:{port}")
        
        # Send get_status command with STX/ETX delimiters
        command = b'\x02{"cmd": "get_status"}\x03'
        sock.send(command)
        print(f"📤 Sent: get_status command")
        
        # Receive response
        response = sock.recv(1024)
        sock.close()
        
        # Strip delimiters and parse JSON
        if response.startswith(b'\x02') and response.endswith(b'\x03'):
            response = response[1:-1]  # Remove STX/ETX
        
        response_str = response.decode('utf-8', errors='ignore')
        print(f"📥 Raw response: {response_str}")
        
        try:
            data = json.loads(response_str)
            print(f"✅ JSON parsed successfully!")
            print(f"📊 Status data:")
            for key, value in data.items():
                print(f"   {key}: {value}")
            return True
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    ip = "192.168.1.130"
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    
    print("🎯 tCam-Mini Station Mode Test")
    print("=" * 40)
    
    success = test_tcam_command(ip)
    
    if success:
        print("\n🎉 SUCCESS! tCam-Mini is working on your home network!")
        print(f"🌐 Access your tCam-Mini at: {ip}:5001")
        print(f"🌐 Web interface (if available): http://{ip}/")
        print("💡 You can now access it without losing internet connectivity!")
    else:
        print("\n❌ Test failed. Device may not be a tCam-Mini or may need more time to boot.")
