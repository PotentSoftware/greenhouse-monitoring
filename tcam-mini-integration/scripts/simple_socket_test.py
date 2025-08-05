#!/usr/bin/env python3
"""
Simple Socket Test - Try different protocols and formats
"""

import socket
import json
import time

def test_raw_socket():
    """Test basic socket communication with different approaches"""
    host = "192.168.4.1"
    port = 5001
    
    print(f"🔗 Testing raw socket to {host}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print("✅ Connected!")
        
        # Test 1: Just send a simple string
        print("\n📤 Test 1: Simple string")
        sock.send(b"hello\n")
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ No response")
        
        # Test 2: Send JSON without newline
        print("\n📤 Test 2: JSON without newline")
        cmd = json.dumps({"cmd": "get_status"})
        sock.send(cmd.encode())
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ No response")
        
        # Test 3: Send JSON with newline
        print("\n📤 Test 3: JSON with newline")
        cmd = json.dumps({"cmd": "get_status"}) + "\n"
        sock.send(cmd.encode())
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ No response")
        
        # Test 4: Send JSON with carriage return + newline
        print("\n📤 Test 4: JSON with \\r\\n")
        cmd = json.dumps({"cmd": "get_status"}) + "\r\n"
        sock.send(cmd.encode())
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ No response")
        
        # Test 5: Try different command
        print("\n📤 Test 5: Different command")
        cmd = json.dumps({"cmd": "ping"}) + "\n"
        sock.send(cmd.encode())
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ No response")
        
        # Test 6: Wait longer for response
        print("\n📤 Test 6: Longer timeout")
        cmd = json.dumps({"cmd": "get_status"}) + "\n"
        sock.send(cmd.encode())
        sock.settimeout(30)  # Wait 30 seconds
        try:
            response = sock.recv(1024)
            print(f"📥 Response: {response}")
        except socket.timeout:
            print("❌ Still no response after 30 seconds")
        
        sock.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Simple Socket Protocol Test")
    print("=" * 40)
    test_raw_socket()
