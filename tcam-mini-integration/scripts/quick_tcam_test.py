#!/usr/bin/env python3
"""
Quick tCam-Mini connection test
Tests basic connectivity without complex workflows
"""

import socket
import json
import time

TCAM_IP = "192.168.4.1"
TCAM_PORT = 5001

def test_basic_connection():
    """Test basic socket connection"""
    print(f"🔧 Quick tCam-Mini Test")
    print(f"Testing connection to {TCAM_IP}:{TCAM_PORT}")
    print()
    
    try:
        print("📡 Creating socket...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print(f"🔗 Connecting to {TCAM_IP}:{TCAM_PORT}...")
        start_time = time.time()
        sock.connect((TCAM_IP, TCAM_PORT))
        connect_time = time.time() - start_time
        print(f"✅ Connected in {connect_time:.2f} seconds")
        
        print("📤 Sending simple command...")
        command = {"cmd": "get_status"}
        message = json.dumps(command) + "\n"
        sock.send(message.encode())
        
        print("📥 Waiting for response (15 second timeout)...")
        sock.settimeout(15)
        response = sock.recv(4096)
        
        if response:
            response_str = response.decode().strip()
            print(f"✅ Got response ({len(response_str)} bytes)")
            print(f"📋 Response: {response_str}")
            
            try:
                json_data = json.loads(response_str)
                print("✅ Valid JSON response")
                if json_data.get("status") == "ok":
                    print("🎉 tCam-Mini is responding correctly!")
                    return True
            except:
                print("⚠️ Response is not valid JSON")
        else:
            print("❌ No response received")
        
        sock.close()
        
    except socket.timeout:
        print("❌ Connection timeout")
        print("💡 Device might be:")
        print("   - Still booting up")
        print("   - Socket server not running")
        print("   - Firmware issue")
    except ConnectionRefusedError:
        print("❌ Connection refused")
        print("💡 Socket server is not running on port 5001")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def test_port_scan():
    """Scan for open ports on the device"""
    print(f"\n🔍 Scanning common ports on {TCAM_IP}...")
    
    common_ports = [23, 80, 443, 5001, 8080, 8888]
    open_ports = []
    
    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((TCAM_IP, port))
            sock.close()
            
            if result == 0:
                open_ports.append(port)
                print(f"✅ Port {port} is open")
            else:
                print(f"❌ Port {port} is closed")
        except:
            print(f"❌ Port {port} - error")
    
    if open_ports:
        print(f"\n📊 Found {len(open_ports)} open ports: {open_ports}")
    else:
        print("\n❌ No open ports found - device might not be responding")

if __name__ == "__main__":
    print("⚠️  Make sure you're connected to tCam-Mini AP first!")
    print("   Run: scripts/connect_tcam_simple.sh")
    print()
    
    input("Press Enter when connected to tCam-Mini AP...")
    
    if test_basic_connection():
        print("\n🎉 SUCCESS: tCam-Mini is working!")
    else:
        print("\n🔍 Running port scan...")
        test_port_scan()
        print("\n💡 Troubleshooting:")
        print("   1. Power cycle the tCam-Mini")
        print("   2. Wait 30 seconds for boot")
        print("   3. Check firmware flash was successful")
        print("   4. Monitor serial output for errors")
