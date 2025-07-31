#!/usr/bin/env python3
"""
Simple tCam-Mini Thermal Image Viewer
Uses direct socket communication to get thermal images from tCam-Mini
"""

import socket
import json
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import time
import sys

class TcamThermalViewer:
    def __init__(self, host='192.168.1.130', port=5001):
        self.host = host
        self.port = port
        self.socket = None
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.im = None
        
        # Temperature conversion parameters for radiometric Lepton
        # Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
        self.LEPTON_RESOLUTION = 0.01  # Resolution: 0.01 K per raw unit
        
        # Create thermal colormap (similar to FLIR)
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        n_bins = 256
        self.thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=n_bins)
        
    def connect(self):
        """Connect to tCam-Mini"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            print(f"Connected to tCam-Mini at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to tCam-Mini: {e}")
            return False
    
    def raw_to_celsius(self, raw_data):
        """Convert raw Lepton thermal data to Celsius
        Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
        """
        celsius_data = (raw_data.astype(float) * self.LEPTON_RESOLUTION) - 273.15
        return celsius_data
    
    def send_command(self, command):
        """Send JSON command to tCam-Mini with proper protocol delimiters"""
        try:
            cmd_json = json.dumps(command)
            # Add tCam protocol delimiters: STX (0x02) + JSON + ETX (0x03)
            cmd_with_delimiters = b'\x02' + cmd_json.encode() + b'\x03'
            self.socket.send(cmd_with_delimiters)
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False
    
    def get_image(self):
        """Request and receive thermal image"""
        try:
            # Send get_image command
            if not self.send_command({"cmd": "get_image"}):
                return None
            
            # Receive response (may be large for image data)
            response = b''
            while True:
                chunk = self.socket.recv(8192)
                if not chunk:
                    break
                response += chunk
                # Check if we have a complete response (ends with ETX)
                if b'\x03' in chunk:
                    break
            
            # Strip STX/ETX delimiters and parse JSON
            response_str = response.decode().strip('\x02\x03')
            data = json.loads(response_str)
            
            # tCam returns image data in 'radiometric' field as base64
            if 'radiometric' in data:
                import base64
                img_data = base64.b64decode(data['radiometric'])
                
                # Convert to numpy array (160x120 16-bit thermal data)
                thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                thermal_raw = thermal_array.reshape((120, 160))
                
                # Convert raw values to temperature in Celsius
                thermal_celsius = self.raw_to_celsius(thermal_raw)
                return thermal_celsius
            else:
                print(f"No thermal data in response: {list(data.keys())}")
                return None
                
        except Exception as e:
            print(f"Failed to get image: {e}")
            return None
    
    def update_frame(self, frame_num):
        """Update function for animation"""
        thermal_data = self.get_image()
        
        if thermal_data is not None:
            if self.im is None:
                self.im = self.ax.imshow(thermal_data, cmap=self.thermal_cmap, aspect='auto')
                self.ax.set_title('tCam-Mini Thermal Image')
                cbar = plt.colorbar(self.im, ax=self.ax)
                cbar.set_label('Temperature (°C)', rotation=270, labelpad=15)
            else:
                self.im.set_array(thermal_data)
                self.im.set_clim(vmin=thermal_data.min(), vmax=thermal_data.max())
            
            # Update title with temperature range
            temp_range = f"{thermal_data.min():.1f}°C to {thermal_data.max():.1f}°C"
            self.ax.set_title(f'tCam-Mini Thermal Image | Range: {temp_range}')
        
        return [self.im] if self.im else []
    
    def start_viewer(self):
        """Start the thermal image viewer"""
        if not self.connect():
            return
        
        try:
            # Start animation
            ani = animation.FuncAnimation(self.fig, self.update_frame, 
                                        interval=1000, blit=False, repeat=True)
            plt.show()
        except KeyboardInterrupt:
            print("Viewer stopped by user")
        finally:
            if self.socket:
                self.socket.close()

def main():
    print("tCam-Mini Thermal Image Viewer")
    print("==============================")
    
    # Try different IP addresses (station mode first, then AP mode)
    hosts_to_try = ['192.168.1.130', '192.168.4.1']
    
    for host in hosts_to_try:
        print(f"Trying to connect to {host}...")
        viewer = TcamThermalViewer(host=host)
        if viewer.connect():
            viewer.socket.close()  # Close test connection
            print(f"Found tCam-Mini at {host}")
            viewer = TcamThermalViewer(host=host)  # Create new instance
            viewer.start_viewer()
            return
        else:
            print(f"No tCam-Mini found at {host}")
    
    print("No tCam-Mini devices found on any of the test addresses")
    print("Make sure:")
    print("1. tCam-Mini is powered on")
    print("2. You're connected to the tCam-Mini WiFi network (tCam-Mini-CDE9)")
    print("3. Or the tCam-Mini is connected to your home network")

if __name__ == "__main__":
    main()
