#!/usr/bin/env python3
"""
Basic tCam-Mini Communication Test Script

This script tests basic communication with tCam-Mini and documents the API.
Run this first to understand how tCam-Mini works before implementing 
advanced features.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration - Test tCam-Mini in dual mode
TCAM_IPS = [
    '192.168.4.1',    # tCam-Mini AP mode IP (primary)
    '192.168.1.246',  # tCam-Mini on home network
    '192.168.1.176',  # Current thermal camera IP
]

TIMEOUT = 5

def test_tcam_connection(ip):
    """Test basic connection to tCam-Mini"""
    print(f"\n=== Testing tCam-Mini at {ip} ===")
    
    # Common tCam-Mini endpoints to test
    endpoints = [
        '/',
        '/status',
        '/camera', 
        '/image',
        '/stream',
        '/config',
        '/api/status',
        '/api/image',
        '/thermal_data'  # Our current endpoint format
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            url = f"http://{ip}{endpoint}"
            print(f"Testing {url}...")
            
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                print(f"  ✅ SUCCESS: {endpoint}")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    results[endpoint] = {
                        'status': 'success',
                        'content_type': 'json',
                        'data': data
                    }
                    print(f"     JSON data: {json.dumps(data, indent=2)[:200]}...")
                except:
                    # Not JSON, check content type
                    content_type = response.headers.get('content-type', 'unknown')
                    results[endpoint] = {
                        'status': 'success', 
                        'content_type': content_type,
                        'size': len(response.content)
                    }
                    print(f"     Content-Type: {content_type}, Size: {len(response.content)} bytes")
            else:
                print(f"  ❌ FAILED: {endpoint} - Status {response.status_code}")
                results[endpoint] = {
                    'status': 'failed',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            print(f"  ⏰ TIMEOUT: {endpoint}")
            results[endpoint] = {'status': 'timeout'}
        except requests.exceptions.ConnectionError:
            print(f"  🔌 CONNECTION ERROR: {endpoint}")
            results[endpoint] = {'status': 'connection_error'}
        except Exception as e:
            print(f"  ❌ ERROR: {endpoint} - {e}")
            results[endpoint] = {'status': 'error', 'message': str(e)}
    
    return results

def save_test_results(ip, results):
    """Save test results to file"""
    timestamp = datetime.now().isoformat()
    filename = f"tcam_test_results_{ip}_{timestamp.replace(':', '-')}.json"
    
    test_data = {
        'timestamp': timestamp,
        'ip_address': ip,
        'test_results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"\n📄 Test results saved to: {filename}")

def main():
    """Main test function"""
    print("🔍 tCam-Mini Basic Communication Test")
    print("=====================================")
    
    found_tcam = False
    
    for ip in TCAM_IPS:
        try:
            # Quick ping test first
            response = requests.get(f"http://{ip}/", timeout=2)
            if response.status_code in [200, 404]:  # 404 is ok, means server is responding
                print(f"\n🎯 Found responding server at {ip}")
                results = test_tcam_connection(ip)
                save_test_results(ip, results)
                found_tcam = True
                
                # If we found working endpoints, show summary
                working_endpoints = [ep for ep, result in results.items() 
                                   if result.get('status') == 'success']
                if working_endpoints:
                    print(f"\n✅ Working endpoints on {ip}:")
                    for ep in working_endpoints:
                        print(f"   - {ep}")
                
        except:
            continue
    
    if not found_tcam:
        print("\n❌ No tCam-Mini found on any of the test IP addresses")
        print("\nTroubleshooting steps:")
        print("1. Verify tCam-Mini is powered on")
        print("2. Check WiFi configuration")
        print("3. Try tCam desktop software to find IP address")
        print("4. Check network connectivity")
        print("5. Try USB connection mode")
    else:
        print(f"\n🎉 tCam-Mini testing complete!")
        print("\nNext steps:")
        print("1. Review the saved test results")
        print("2. Identify the correct API endpoints")
        print("3. Test thermal image capture")
        print("4. Document the data format")

if __name__ == "__main__":
    main()