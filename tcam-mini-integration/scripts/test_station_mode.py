#!/usr/bin/env python3
"""
Comprehensive test for tCam-Mini in station mode
Tests socket connectivity, command responses, and thermal image retrieval
"""

import socket
import json
import time
import sys

TCAM_IP = "192.168.1.130"
TCAM_PORT = 5001

def test_socket_connection():
    """Test basic socket connectivity"""
    print("🔌 Testing socket connection...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((TCAM_IP, TCAM_PORT))
        sock.close()
        if result == 0:
            print(f"✅ Socket connection successful to {TCAM_IP}:{TCAM_PORT}")
            return True
        else:
            print(f"❌ Socket connection failed (error {result})")
            return False
    except Exception as e:
        print(f"❌ Socket connection error: {e}")
        return False

def send_command(command, timeout=10):
    """Send a command and get response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((TCAM_IP, TCAM_PORT))
        
        cmd_json = json.dumps({'cmd': command})
        # Add tCam protocol delimiters: STX (0x02) + JSON + ETX (0x03)
        cmd_with_delimiters = b'\x02' + cmd_json.encode() + b'\x03'
        print(f"📤 Sent: {cmd_json} (with STX/ETX delimiters)")
        sock.send(cmd_with_delimiters)
        
        # Receive response
        response = ''
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data = sock.recv(4096).decode()
                if data:
                    response += data
                    # Check if we have a complete JSON response
                    if response.count('{') > 0 and response.count('}') >= response.count('{'):
                        break
            except socket.timeout:
                break
        
        sock.close()
        return response.strip()
        
    except Exception as e:
        print(f"❌ Command error: {e}")
        return None

def test_commands():
    """Test various tCam commands"""
    commands = [
        ('get_status', 5),
        ('get_camera_info', 5),
        ('get_image', 15),  # Longer timeout for image
    ]
    
    results = {}
    
    for command, timeout in commands:
        print(f"\n🧪 Testing '{command}' command...")
        response = send_command(command, timeout)
        
        if response:
            print(f"📥 Received: {response[:200]}{'...' if len(response) > 200 else ''}")
            # Strip STX/ETX delimiters if present and try to parse as JSON
            try:
                # Remove STX (0x02) and ETX (0x03) delimiters
                clean_response = response.strip('\x02\x03')
                if clean_response:
                    result = json.loads(clean_response)
                    results[command] = result
                    print(f"✅ {command} successful!")
                    
                    # Print relevant info based on response type
                    if 'status' in result:
                        print(f"   Camera: {result['status'].get('Camera', 'Unknown')}")
                        print(f"   Model: {result['status'].get('Model', 'Unknown')}")
                        print(f"   Version: {result['status'].get('Version', 'Unknown')}")
                    elif 'cam_info' in result:
                        print(f"   Info: {result['cam_info'].get('info_string', 'No info')}")
                    elif 'image' in result or 'metadata' in result:
                        if 'metadata' in result:
                            print(f"   Camera: {result['metadata'].get('Camera', 'Unknown')}")
                        if 'radiometric' in result:
                            print(f"   Image data length: {len(result.get('radiometric', ''))}")
                else:
                    print("⚠️  Empty response after delimiter removal")
                    results[command] = {'error': 'empty_response'}
                    
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                results[command] = {'error': 'invalid_json', 'response': response}
        else:
            print(f"❌ No response for {command}")
            results[command] = {'error': 'no_response'}
    
    return results

def main():
    print("🎯 tCam-Mini Station Mode Test")
    print("=" * 50)
    print(f"Target: {TCAM_IP}:{TCAM_PORT}")
    print()
    
    # Test 1: Basic connectivity
    if not test_socket_connection():
        print("\n❌ Basic connectivity failed. Exiting.")
        return False
    
    # Test 2: Command interface
    print("\n📋 Testing command interface...")
    results = test_commands()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    success_count = 0
    total_count = len(results)
    
    for command, result in results.items():
        if isinstance(result, dict) and 'error' not in result:
            print(f"✅ {command}: SUCCESS")
            success_count += 1
        else:
            print(f"❌ {command}: FAILED")
            if isinstance(result, dict) and 'error' in result:
                print(f"   Error: {result['error']}")
    
    print(f"\n🎯 Overall: {success_count}/{total_count} commands successful")
    
    if success_count > 0:
        print("🎉 Station mode is working! Device is accessible on home network.")
        print(f"💡 You can now access the device at http://{TCAM_IP} in your browser")
        print(f"💡 Or run: python3 tcam_thermal_viewer.py")
        return True
    else:
        print("⚠️  Station mode connected but commands not responding")
        print("💡 This may indicate SPI communication issues or service startup problems")
        return False

if __name__ == "__main__":
    main()
