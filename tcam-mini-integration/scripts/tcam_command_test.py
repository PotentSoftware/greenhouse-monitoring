#!/usr/bin/env python3
"""
tCam-Mini Command Interface Tester
Tests socket communication and tries to trigger image capture
"""

import socket
import json
import time
import sys

def send_command(sock, command_dict):
    """Send a JSON command to tCam-Mini and get response"""
    try:
        # Send command
        cmd_json = json.dumps(command_dict) + '\n'
        print(f"→ Sending: {cmd_json.strip()}")
        sock.send(cmd_json.encode())
        
        # Receive response
        response = sock.recv(4096).decode()
        print(f"← Received: {response.strip()}")
        
        # Try to parse as JSON
        try:
            response_data = json.loads(response)
            return response_data
        except json.JSONDecodeError:
            return {"raw_response": response}
            
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return None

def test_tcam_commands(host='192.168.4.1', port=5001):
    """Test various tCam-Mini commands"""
    print(f"🔌 Connecting to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("✅ Connected successfully!")
        
        # Test 1: Get status
        print("\n📊 Testing get_status command...")
        response = send_command(sock, {"command": "get_status"})
        
        # Test 2: Get camera info
        print("\n📷 Testing get_camera_info command...")
        response = send_command(sock, {"command": "get_camera_info"})
        
        # Test 3: Get single image
        print("\n🖼️  Testing get_image command...")
        response = send_command(sock, {"command": "get_image"})
        
        # Test 4: Try to start streaming
        print("\n🎥 Testing start_stream command...")
        response = send_command(sock, {"command": "start_stream"})
        
        # Wait a bit for potential stream data
        print("\n⏳ Waiting for stream data...")
        time.sleep(2)
        
        # Test 5: Stop streaming
        print("\n⏹️  Testing stop_stream command...")
        response = send_command(sock, {"command": "stop_stream"})
        
        # Test 6: Get configuration
        print("\n⚙️  Testing get_config command...")
        response = send_command(sock, {"command": "get_config"})
        
        sock.close()
        print("\n✅ All tests completed!")
        
    except ConnectionRefusedError:
        print(f"❌ Connection refused to {host}:{port}")
        print("Make sure you're connected to the tCam-Mini-CDE9 WiFi network")
        return False
    except socket.timeout:
        print(f"❌ Connection timeout to {host}:{port}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    return True

def main():
    print("tCam-Mini Command Interface Tester")
    print("=" * 50)
    
    # Check if we should test a specific host
    host = '192.168.4.1'
    if len(sys.argv) > 1:
        host = sys.argv[1]
        print(f"Using custom host: {host}")
    
    # Test commands
    success = test_tcam_commands(host)
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure tCam-Mini is powered on")
        print("2. Connect to tCam-Mini-CDE9 WiFi network:")
        print("   nmcli device wifi connect 'tCam-Mini-CDE9'")
        print("3. Check device is responding:")
        print("   ping 192.168.4.1")
        print("4. Check serial output for errors:")
        print("   idf.py monitor")

if __name__ == "__main__":
    main()
