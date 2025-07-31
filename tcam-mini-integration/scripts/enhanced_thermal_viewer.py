#!/usr/bin/env python3
"""
Enhanced tCam-Mini Thermal Image Viewer
Features:
- Live thermal imaging with temperature display
- Temperature statistics (min/max/avg)
- Crosshair cursor with temperature readout
- Save thermal images
- Temperature scale bar
- Device status display
"""

import socket
import json
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button
import time
import sys
from datetime import datetime
import base64

class EnhancedTcamViewer:
    def __init__(self, host='192.168.1.130', port=5001):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
        # Create figure with dark theme
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 8), facecolor='#1a1a1a')
        self.fig.suptitle('🌡️ tCam-Mini Enhanced Thermal Viewer', fontsize=16, fontweight='bold', color='#4caf50')
        
        # Create subplots with grid layout
        self.ax_thermal = plt.subplot2grid((2, 3), (0, 0), colspan=2, rowspan=2, facecolor='#2a2a2a')
        self.ax_stats = plt.subplot2grid((2, 3), (0, 2), facecolor='#2a2a2a')
        self.ax_controls = plt.subplot2grid((2, 3), (1, 2), facecolor='#2a2a2a')
        
        self.im = None
        self.thermal_data = None
        self.device_info = {}
        
        # Create thermal colormap
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        self.thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
        
        # Temperature conversion parameters for radiometric Lepton
        # Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
        self.LEPTON_RESOLUTION = 0.01  # Resolution: 0.01 K per raw unit
        
        # Statistics (in Celsius)
        self.temp_min = 0.0
        self.temp_max = 0.0
        self.temp_avg = 0.0
        self.cursor_temp = 0.0
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface with dark theme"""
        self.ax_thermal.set_title('🌡️ tCam-Mini Thermal Image', fontsize=14, fontweight='bold', color='#4caf50')
        self.ax_thermal.set_xlabel('Pixel X', color='#e0e0e0')
        self.ax_thermal.set_ylabel('Pixel Y', color='#e0e0e0')
        self.ax_thermal.tick_params(colors='#e0e0e0')
        
        # Stats display
        self.ax_stats.set_title('📊 Temperature Stats', fontsize=12, fontweight='bold', color='#4caf50')
        self.ax_stats.axis('off')
        self.stats_text = self.ax_stats.text(0.1, 0.8, '', fontsize=10, 
                                           verticalalignment='top', fontfamily='monospace', color='#e0e0e0')
        
        # Controls
        self.ax_controls.set_title('🎮 Controls', fontsize=12, fontweight='bold', color='#4caf50')
        self.ax_controls.axis('off')
        
        # Add save button
        self.save_button = Button(plt.axes([0.75, 0.02, 0.1, 0.04]), 'Save Image')
        self.save_button.on_clicked(self.save_image)
        
        # Add status button
        self.status_button = Button(plt.axes([0.85, 0.02, 0.1, 0.04]), 'Get Status')
        self.status_button.on_clicked(self.get_device_status)
        
        # Mouse click handler for temperature readout
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
    def connect(self):
        """Connect to tCam-Mini"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"✅ Connected to tCam-Mini at {self.host}:{self.port}")
            
            # Get initial device status
            self.get_device_status(None)
            return True
        except Exception as e:
            print(f"❌ Failed to connect to tCam-Mini: {e}")
            self.connected = False
            return False
    
    def send_command(self, command):
        """Send JSON command with proper delimiters"""
        if not self.connected:
            return False
            
        try:
            cmd_json = json.dumps(command)
            cmd_with_delimiters = b'\x02' + cmd_json.encode() + b'\x03'
            self.socket.send(cmd_with_delimiters)
            return True
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            self.connected = False
            return False
    
    def receive_response(self):
        """Receive and parse response with delimiters"""
        try:
            response = b''
            while True:
                chunk = self.socket.recv(8192)
                if not chunk:
                    break
                response += chunk
                if b'\x03' in chunk:
                    break
            
            response_str = response.decode().strip('\x02\x03')
            return json.loads(response_str)
        except Exception as e:
            print(f"❌ Failed to receive response: {e}")
            return None
    
    def raw_to_celsius(self, raw_data):
        """Convert raw Lepton thermal data to Celsius
        
        Args:
            raw_data: numpy array of 16-bit raw thermal values (Kelvin × 100)
            
        Returns:
            numpy array of temperatures in Celsius
        """
        # Convert raw values to temperature for radiometric Lepton
        # Formula: T(°C) = (raw × resolution) - 273.15
        # Raw data is in Kelvin × 100, so resolution = 0.01
        celsius_data = (raw_data.astype(float) * self.LEPTON_RESOLUTION) - 273.15
        return celsius_data
    
    def get_image(self):
        """Get thermal image from device"""
        if not self.send_command({"cmd": "get_image"}):
            return None
            
        data = self.receive_response()
        if not data or 'radiometric' not in data:
            return None
            
        try:
            img_data = base64.b64decode(data['radiometric'])
            thermal_array = np.frombuffer(img_data, dtype=np.uint16)
            thermal_raw = thermal_array.reshape((120, 160))
            
            # Convert raw data to temperature in Celsius
            thermal_celsius = self.raw_to_celsius(thermal_raw)
            
            # Store metadata
            if 'metadata' in data:
                self.device_info.update(data['metadata'])
            
            return thermal_celsius
        except Exception as e:
            print(f"❌ Failed to process image: {e}")
            return None
    
    def get_device_status(self, event):
        """Get device status"""
        if not self.send_command({"cmd": "get_status"}):
            return
            
        data = self.receive_response()
        if data and 'status' in data:
            self.device_info.update(data['status'])
            print(f"📊 Device: {self.device_info.get('Camera', 'Unknown')}")
            print(f"📊 Version: {self.device_info.get('Version', 'Unknown')}")
    
    def calculate_stats(self, thermal_data):
        """Calculate temperature statistics"""
        if thermal_data is not None:
            self.temp_min = np.min(thermal_data)
            self.temp_max = np.max(thermal_data)
            self.temp_avg = np.mean(thermal_data)
    
    def update_stats_display(self):
        """Update statistics display"""
        stats_text = f"""Device: {self.device_info.get('Camera', 'Unknown')}
Version: {self.device_info.get('Version', 'Unknown')}
Status: {'Connected' if self.connected else 'Disconnected'}

Temperature Stats (°C):
Min: {self.temp_min:.1f}°C
Max: {self.temp_max:.1f}°C
Avg: {self.temp_avg:.1f}°C
Range: {self.temp_max - self.temp_min:.1f}°C

Cursor: {self.cursor_temp:.1f}°C

Time: {datetime.now().strftime('%H:%M:%S')}"""
        
        self.stats_text.set_text(stats_text)
    
    def on_click(self, event):
        """Handle mouse clicks for temperature readout"""
        if event.inaxes == self.ax_thermal and self.thermal_data is not None:
            if event.xdata is not None and event.ydata is not None:
                x, y = int(event.xdata), int(event.ydata)
                if 0 <= x < 160 and 0 <= y < 120:
                    self.cursor_temp = self.thermal_data[y, x]
    
    def save_image(self, event):
        """Save current thermal image"""
        if self.thermal_data is not None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'thermal_image_{timestamp}.png'
            
            # Save the matplotlib figure
            self.fig.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"💾 Saved thermal image: {filename}")
            
            # Also save raw data as numpy array
            np_filename = f'thermal_data_{timestamp}.npy'
            np.save(np_filename, self.thermal_data)
            print(f"💾 Saved raw data: {np_filename}")
    
    def update_frame(self, frame_num):
        """Update function for animation"""
        if not self.connected:
            return []
            
        thermal_data = self.get_image()
        
        if thermal_data is not None:
            self.thermal_data = thermal_data
            self.calculate_stats(thermal_data)
            
            if self.im is None:
                self.im = self.ax_thermal.imshow(thermal_data, cmap=self.thermal_cmap, 
                                                aspect='auto', interpolation='nearest')
                # Add colorbar with dark theme styling
                cbar = plt.colorbar(self.im, ax=self.ax_thermal, fraction=0.046, pad=0.04)
                cbar.set_label('Temperature (°C)', rotation=270, labelpad=15, color='#e0e0e0', fontweight='bold')
                cbar.ax.tick_params(colors='#e0e0e0')
            else:
                self.im.set_array(thermal_data)
                self.im.set_clim(vmin=thermal_data.min(), vmax=thermal_data.max())
            
            self.update_stats_display()
        
        return [self.im] if self.im else []
    
    def start_viewer(self):
        """Start the enhanced thermal viewer"""
        if not self.connect():
            print("❌ Cannot start viewer - connection failed")
            return
        
        try:
            print("🌡️  Enhanced tCam-Mini Thermal Viewer Started")
            print("📌 Click on thermal image to get temperature at cursor")
            print("💾 Use 'Save Image' button to save thermal images")
            print("📊 Use 'Get Status' button to refresh device info")
            print("⌨️  Press Ctrl+C to exit")
            
            # Start animation
            ani = animation.FuncAnimation(self.fig, self.update_frame, 
                                        interval=1000, blit=False, repeat=True)
            plt.tight_layout()
            plt.show()
        except KeyboardInterrupt:
            print("\n👋 Viewer stopped by user")
        finally:
            if self.socket:
                self.socket.close()

def main():
    print("🌡️  Enhanced tCam-Mini Thermal Viewer")
    print("=" * 50)
    
    # Try to connect
    viewer = EnhancedTcamViewer()
    viewer.start_viewer()

if __name__ == "__main__":
    main()
