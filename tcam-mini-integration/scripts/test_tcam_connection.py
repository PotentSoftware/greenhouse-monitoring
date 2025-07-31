#!/usr/bin/env python3
"""
Test tCam-Mini connectivity and socket communication
"""

import socket
import json
import time
import sys

def test_tcam_connection(host='192.168.4.1', port=5001, timeout=5):
    """Test if we can connect to tCam-Mini socket service"""
    print(f"Testing connection to {host}:{port}...")
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Try to connect
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print(f"✅ Successfully connected to {host}:{port}")
            
            # Try to send a simple command
            try:
                # Send get_status command
                cmd = {"command": "get_status"}
                cmd_json = json.dumps(cmd) + '\n'
                sock.send(cmd_json.encode())
                
                # Try to receive response
                response = sock.recv(1024).decode()
                print(f"📡 Received response: {response[:100]}...")
                
                return True
                
            except Exception as e:
                print(f"⚠️  Connected but communication failed: {e}")
                return False
                
        else:
            print(f"❌ Failed to connect to {host}:{port} (error {result})")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
        
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    print("tCam-Mini Connection Test")
    print("=" * 40)
    
    # Test default AP address
    if test_tcam_connection('192.168.4.1', 5001):
        print("\n🎉 tCam-Mini is accessible!")
        print("You can now run the thermal viewer with:")
        print("python3 tcam_thermal_viewer.py")
    else:
        print("\n💡 tCam-Mini not accessible on AP network.")
        print("Make sure you're connected to the tCam-Mini-CDE9 WiFi network.")
        
        # Test if we can reach it on home network (if configured)
        print("\nTesting if tCam-Mini is on home network...")
        # Try common IP ranges
        for ip in ['192.168.1.246', '192.168.1.100', '192.168.0.100']:
            if test_tcam_connection(ip, 5001, timeout=2):
                print(f"\n🎉 Found tCam-Mini at {ip}!")
                print(f"You can run the thermal viewer with:")
                print(f"python3 tcam_thermal_viewer.py --host {ip}")
                return
                
        print("\n❓ tCam-Mini not found on common home network addresses.")

if __name__ == "__main__":
    main()
