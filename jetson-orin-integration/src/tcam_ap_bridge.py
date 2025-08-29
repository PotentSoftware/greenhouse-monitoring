#!/usr/bin/env python3
"""
tCam-Mini AP Mode Bridge
Connects to tCam-Mini in AP mode to fetch thermal data
"""

import socket
import json
import numpy as np
import subprocess
import time
import logging

logger = logging.getLogger(__name__)

class TcamAPBridge:
    def __init__(self, tcam_ssid="tCam-Mini-CDE9", tcam_ip="192.168.4.1", tcam_port=5001):
        self.tcam_ssid = tcam_ssid
        self.tcam_ip = tcam_ip
        self.tcam_port = tcam_port
        self.home_wifi_ssid = None
        self.connected_to_tcam = False
        
    def get_current_wifi(self):
        """Get currently connected WiFi network"""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], 
                                  capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line.startswith('yes:'):
                    return line.split(':', 1)[1]
            return None
        except Exception as e:
            logger.error(f"Error getting current WiFi: {e}")
            return None
    
    def connect_to_tcam_ap(self):
        """Connect to tCam-Mini AP"""
        try:
            # Save current WiFi
            self.home_wifi_ssid = self.get_current_wifi()
            logger.info(f"Current WiFi: {self.home_wifi_ssid}")
            
            # Connect to tCam-Mini AP
            logger.info(f"Connecting to {self.tcam_ssid}...")
            result = subprocess.run(['nmcli', 'device', 'wifi', 'connect', self.tcam_ssid],
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.connected_to_tcam = True
                time.sleep(2)  # Wait for connection to stabilize
                logger.info("Connected to tCam-Mini AP")
                return True
            else:
                logger.error(f"Failed to connect: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to tCam AP: {e}")
            return False
    
    def restore_home_wifi(self):
        """Restore connection to home WiFi"""
        try:
            if self.home_wifi_ssid:
                logger.info(f"Restoring connection to {self.home_wifi_ssid}...")
                subprocess.run(['nmcli', 'connection', 'up', self.home_wifi_ssid],
                             capture_output=True, text=True)
                self.connected_to_tcam = False
                time.sleep(2)
                logger.info("Restored home WiFi connection")
        except Exception as e:
            logger.error(f"Error restoring WiFi: {e}")
    
    def send_tcam_command(self, command_dict):
        """Send command to tCam-Mini"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.tcam_ip, self.tcam_port))
            
            # Send command with STX/ETX delimiters
            cmd_json = json.dumps(command_dict)
            cmd_with_delimiters = b'\x02' + cmd_json.encode() + b'\x03'
            sock.send(cmd_with_delimiters)
            
            # Receive response
            response = b''
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response += chunk
                if b'\x03' in chunk:
                    break
            
            sock.close()
            
            # Parse response
            if response.startswith(b'\x02') and b'\x03' in response:
                etx_pos = response.find(b'\x03')
                json_response = response[1:etx_pos].decode()
                return json.loads(json_response)
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return None
    
    def get_thermal_image_ap_mode(self):
        """Get thermal image by temporarily connecting to AP"""
        thermal_data = None
        
        try:
            # Connect to tCam AP
            if not self.connect_to_tcam_ap():
                return None
            
            # Get thermal image
            response = self.send_tcam_command({"cmd": "get_image"})
            
            if response and 'radiometric' in response:
                import base64
                img_data = base64.b64decode(response['radiometric'])
                thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                thermal_raw = thermal_array.reshape((120, 160))
                
                # Convert Kelvin*100 to Celsius
                thermal_data = (thermal_raw.astype(float) * 0.01) - 273.15
                
        except Exception as e:
            logger.error(f"Error getting thermal image: {e}")
            
        finally:
            # Always restore home WiFi
            self.restore_home_wifi()
            
        return thermal_data
    
    def get_thermal_stats_ap_mode(self):
        """Get thermal statistics by temporarily connecting to AP"""
        stats = None
        
        try:
            # Connect to tCam AP
            if not self.connect_to_tcam_ap():
                return None
            
            # Get device status
            response = self.send_tcam_command({"cmd": "get_status"})
            
            if response:
                stats = response
                
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            
        finally:
            # Always restore home WiFi
            self.restore_home_wifi()
            
        return stats


# Alternative: Mock thermal data generator for testing
def generate_mock_thermal_data():
    """Generate realistic mock thermal data"""
    # Base temperature field
    base_temp = 22.0
    thermal_data = np.random.normal(base_temp, 0.5, (120, 160))
    
    # Add some hot spots (plants under grow lights)
    for _ in range(3):
        x = np.random.randint(20, 140)
        y = np.random.randint(20, 100)
        for i in range(max(0, x-10), min(160, x+10)):
            for j in range(max(0, y-10), min(120, y+10)):
                dist = np.sqrt((i-x)**2 + (j-y)**2)
                if dist < 10:
                    thermal_data[j, i] += (10 - dist) * 0.8
    
    # Add cooler areas (shadows)
    for _ in range(2):
        x = np.random.randint(20, 140)
        y = np.random.randint(20, 100)
        for i in range(max(0, x-15), min(160, x+15)):
            for j in range(max(0, y-15), min(120, y+15)):
                dist = np.sqrt((i-x)**2 + (j-y)**2)
                if dist < 15:
                    thermal_data[j, i] -= (15 - dist) * 0.3
    
    # Ensure reasonable temperature range
    thermal_data = np.clip(thermal_data, 18.0, 35.0)
    
    return thermal_data


if __name__ == "__main__":
    # Test the AP bridge
    logging.basicConfig(level=logging.INFO)
    
    bridge = TcamAPBridge()
    
    print("Testing tCam-Mini AP Bridge...")
    print("This will temporarily disconnect from your home WiFi!")
    
    # Test thermal image capture
    thermal_data = bridge.get_thermal_image_ap_mode()
    
    if thermal_data is not None:
        print(f"✅ Got thermal image: {thermal_data.shape}")
        print(f"   Temperature range: {thermal_data.min():.1f}°C to {thermal_data.max():.1f}°C")
    else:
        print("❌ Failed to get thermal image")
        print("   Using mock data instead")
        thermal_data = generate_mock_thermal_data()
        print(f"   Mock data range: {thermal_data.min():.1f}°C to {thermal_data.max():.1f}°C")
