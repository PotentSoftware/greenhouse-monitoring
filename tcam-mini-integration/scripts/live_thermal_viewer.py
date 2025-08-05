#!/usr/bin/env python3
"""
Live Thermal Viewer for tCam-Mini
Uses correct protocol with STX/ETX delimiters for real-time thermal imaging
"""

import socket
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button
import time
import threading
import queue
import os
from datetime import datetime
import cv2

class LiveThermalViewer:
    def __init__(self, tcam_ip="192.168.1.130", tcam_port=5001):
        self.tcam_ip = tcam_ip
        self.tcam_port = tcam_port
        self.thermal_queue = queue.Queue(maxsize=5)
        self.running = False
        self.capturing = False
        self.latest_thermal_data = None
        
        # Desktop path for saving images
        self.desktop_path = os.path.expanduser("~/Desktop")
        if not os.path.exists(self.desktop_path):
            self.desktop_path = os.path.expanduser("~")  # Fallback to home
        
        # Create custom thermal colormap
        colors = ['#000080', '#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF8000', '#FF0000', '#FFFFFF']
        self.thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
        
        # Setup matplotlib
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(14, 6))
        self.fig.suptitle('tCam-Mini Live Thermal Viewer', fontsize=16, color='white')
        
        # Add capture button
        self.setup_capture_button()
        
        # Initialize plots
        self.thermal_im = None
        self.temp_text = None
        
    def send_command(self, command):
        """Send command with correct STX/ETX protocol"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((self.tcam_ip, self.tcam_port))
            
            # Format: STX + JSON + ETX
            json_cmd = json.dumps(command)
            message = b'\x02' + json_cmd.encode('utf-8') + b'\x03'
            
            sock.send(message)
            
            # Read response
            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if b'\x03' in response:  # ETX found
                    break
            
            sock.close()
            
            # Parse response (remove STX/ETX)
            if response.startswith(b'\x02') and b'\x03' in response:
                etx_pos = response.find(b'\x03')
                json_data = response[1:etx_pos].decode('utf-8')
                return json.loads(json_data)
            
            return None
            
        except Exception as e:
            print(f"Command error: {e}")
            return None
    
    def decode_thermal_data(self, radiometric_data):
        """Decode base64 thermal data to temperature array"""
        try:
            # Decode base64
            thermal_bytes = base64.b64decode(radiometric_data)
            
            # Convert to 16-bit values (Lepton 3.5 is 160x120, 16-bit per pixel)
            thermal_raw = np.frombuffer(thermal_bytes, dtype=np.uint16)
            
            # Reshape to 120x160 (Lepton 3.5 resolution)
            if len(thermal_raw) >= 19200:  # 120 * 160
                thermal_array = thermal_raw[:19200].reshape(120, 160)
                
                # Convert raw values to temperature (Kelvin to Celsius)
                # Lepton raw values are in centi-Kelvin
                temp_celsius = (thermal_array / 100.0) - 273.15
                
                return temp_celsius
            
        except Exception as e:
            print(f"Decode error: {e}")
        
        return None
    
    def thermal_capture_thread(self):
        """Background thread to capture thermal images"""
        while self.running:
            try:
                # Get thermal image
                response = self.send_command({"cmd": "get_image"})
                
                if response and "radiometric" in response:
                    thermal_data = self.decode_thermal_data(response["radiometric"])
                    
                    if thermal_data is not None:
                        # Add metadata
                        metadata = response.get("metadata", {})
                        thermal_info = {
                            'data': thermal_data,
                            'timestamp': time.time(),
                            'camera': metadata.get('Camera', 'Unknown'),
                            'version': metadata.get('Version', 'Unknown'),
                            'min_temp': np.min(thermal_data),
                            'max_temp': np.max(thermal_data),
                            'avg_temp': np.mean(thermal_data)
                        }
                        
                        # Add to queue (non-blocking)
                        try:
                            self.thermal_queue.put_nowait(thermal_info)
                        except queue.Full:
                            # Remove oldest frame if queue is full
                            try:
                                self.thermal_queue.get_nowait()
                                self.thermal_queue.put_nowait(thermal_info)
                            except queue.Empty:
                                pass
                
                time.sleep(0.1)  # 10 FPS max
                
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(1)
    
    def animate(self, frame):
        """Animation function for matplotlib"""
        try:
            # Get latest thermal data
            thermal_info = self.thermal_queue.get_nowait()
            thermal_data = thermal_info['data']
            
            # Update thermal image
            if self.thermal_im is None:
                self.thermal_im = self.ax1.imshow(thermal_data, cmap=self.thermal_cmap, 
                                                 interpolation='bilinear', aspect='auto')
                self.ax1.set_title('Thermal Image', color='white')
                self.ax1.set_xlabel('Pixel X', color='white')
                self.ax1.set_ylabel('Pixel Y', color='white')
                
                # Add colorbar
                cbar = plt.colorbar(self.thermal_im, ax=self.ax1)
                cbar.set_label('Temperature (°C)', color='white')
                cbar.ax.yaxis.set_tick_params(color='white')
                plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            else:
                self.thermal_im.set_array(thermal_data)
                self.thermal_im.set_clim(vmin=np.min(thermal_data), vmax=np.max(thermal_data))
            
            # Update temperature statistics
            self.ax2.clear()
            self.ax2.set_facecolor('black')
            
            # Temperature histogram
            self.ax2.hist(thermal_data.flatten(), bins=50, color='orange', alpha=0.7, edgecolor='white')
            self.ax2.set_title('Temperature Distribution', color='white')
            self.ax2.set_xlabel('Temperature (°C)', color='white')
            self.ax2.set_ylabel('Pixel Count', color='white')
            self.ax2.tick_params(colors='white')
            
            # Add statistics text
            capture_status = "🔴 CAPTURING..." if self.capturing else "⚪ Ready"
            stats_text = f"""Camera: {thermal_info['camera']}
Version: {thermal_info['version']}
Min: {thermal_info['min_temp']:.1f}°C
Max: {thermal_info['max_temp']:.1f}°C
Avg: {thermal_info['avg_temp']:.1f}°C
FPS: {1.0/(time.time()-thermal_info['timestamp']+0.001):.1f}
Status: {capture_status}"""
            
            self.ax2.text(0.02, 0.98, stats_text, transform=self.ax2.transAxes, 
                         verticalalignment='top', color='white', fontsize=10,
                         bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
            
            # Store latest thermal data for capture
            self.latest_thermal_data = thermal_info
            
        except queue.Empty:
            pass  # No new data
        except Exception as e:
            print(f"Animation error: {e}")
        
        return []
    
    def start_viewer(self):
        """Start the live thermal viewer"""
        print(f"🔥 Starting Live Thermal Viewer")
        print(f"📡 Connecting to tCam-Mini at {self.tcam_ip}:{self.tcam_port}")
        
        # Test connection
        status = self.send_command({"cmd": "get_status"})
        if not status:
            print("❌ Cannot connect to tCam-Mini!")
            print("Make sure you're connected to tCam-Mini AP mode")
            return
        
        print(f"✅ Connected to {status['status']['Camera']}")
        print(f"📷 Version: {status['status']['Version']}")
        
        # Start capture thread
        self.running = True
        capture_thread = threading.Thread(target=self.thermal_capture_thread, daemon=True)
        capture_thread.start()
        
        # Start animation
        ani = animation.FuncAnimation(self.fig, self.animate, interval=100, blit=False)
        
        print("🎬 Live viewer started! Close window to stop.")
        plt.tight_layout()
        plt.show()
        
        # Cleanup
        self.running = False
    
    def setup_capture_button(self):
        """Setup the capture button"""
        # Create button axes
        button_ax = plt.axes([0.45, 0.02, 0.1, 0.05])  # [left, bottom, width, height]
        self.capture_button = Button(button_ax, '📸 Capture 10', color='darkred', hovercolor='red')
        self.capture_button.label.set_color('white')
        self.capture_button.on_clicked(self.capture_sequence)
    
    def capture_sequence(self, event):
        """Capture 10 thermal images to Desktop"""
        if self.capturing:
            print("⏳ Capture already in progress...")
            return
        
        # Start capture in background thread
        capture_thread = threading.Thread(target=self._capture_worker, daemon=True)
        capture_thread.start()
    
    def _capture_worker(self):
        """Background worker to capture 10 images"""
        self.capturing = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"📸 Starting capture sequence: 10 images")
        print(f"💾 Saving to: {self.desktop_path}")
        
        try:
            for i in range(10):
                # Get fresh thermal image
                response = self.send_command({"cmd": "get_image"})
                
                if response and "radiometric" in response:
                    thermal_data = self.decode_thermal_data(response["radiometric"])
                    
                    if thermal_data is not None:
                        # Save in multiple formats for maximum utility
                        base_filename = f"thermal_{timestamp}_{i+1:02d}"
                        
                        # 1. Raw temperature data as NPY (best for analysis)
                        npy_path = os.path.join(self.desktop_path, f"{base_filename}.npy")
                        np.save(npy_path, thermal_data)
                        
                        # 2. Raw temperature as 16-bit TIFF (scientific standard)
                        tiff_path = os.path.join(self.desktop_path, f"{base_filename}_raw.tiff")
                        self.save_raw_tiff(thermal_data, tiff_path)
                        
                        # 3. Visual thermal image as PNG (beautiful, lossless)
                        png_path = os.path.join(self.desktop_path, f"{base_filename}.png")
                        self.save_thermal_image(thermal_data, png_path, response.get("metadata", {}))
                        
                        print(f"✅ Captured {i+1}/10: {base_filename} (NPY+TIFF+PNG)")
                    else:
                        print(f"❌ Failed to decode image {i+1}/10")
                else:
                    print(f"❌ Failed to get image {i+1}/10")
                
                # Wait between captures
                if i < 9:  # Don't wait after last image
                    time.sleep(0.5)
            
            print(f"🎉 Capture complete! 10 images saved to Desktop")
            print(f"📁 Visual: thermal_{timestamp}_01.png through thermal_{timestamp}_10.png")
            print(f"📊 Raw NPY: thermal_{timestamp}_01.npy through thermal_{timestamp}_10.npy")
            print(f"🔬 Raw TIFF: thermal_{timestamp}_01_raw.tiff through thermal_{timestamp}_10_raw.tiff")
            
        except Exception as e:
            print(f"❌ Capture error: {e}")
        
        finally:
            self.capturing = False
    
    def save_thermal_image(self, thermal_data, filepath, metadata):
        """Save thermal data as a visual image"""
        try:
            # Create figure for saving
            fig, ax = plt.subplots(figsize=(8, 6), facecolor='black')
            
            # Plot thermal image
            im = ax.imshow(thermal_data, cmap=self.thermal_cmap, interpolation='bilinear')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('Temperature (°C)', color='white')
            cbar.ax.yaxis.set_tick_params(color='white')
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
            
            # Styling
            ax.set_title(f'Thermal Image - {metadata.get("Camera", "tCam-Mini")}', color='white')
            ax.set_xlabel('Pixel X', color='white')
            ax.set_ylabel('Pixel Y', color='white')
            ax.tick_params(colors='white')
            
            # Add temperature stats
            stats_text = f'Min: {np.min(thermal_data):.1f}°C\nMax: {np.max(thermal_data):.1f}°C\nAvg: {np.mean(thermal_data):.1f}°C'
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', color='white', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='black', alpha=0.8))
            
            # Save with tight layout
            plt.tight_layout()
            plt.savefig(filepath, facecolor='black', dpi=150, bbox_inches='tight')
            plt.close(fig)
            
        except Exception as e:
            print(f"❌ Error saving image {filepath}: {e}")
    
    def save_raw_tiff(self, thermal_data, filepath):
        """Save raw temperature data as 16-bit TIFF"""
        try:
            # Convert temperature to 16-bit integer (preserve precision)
            # Scale from Celsius to avoid negative values: (temp + 100) * 100
            # This gives us 0.01°C precision in 16-bit format
            temp_scaled = ((thermal_data + 100.0) * 100.0).astype(np.uint16)
            
            # Save as 16-bit TIFF
            from PIL import Image
            img = Image.fromarray(temp_scaled, mode='I;16')
            img.save(filepath, format='TIFF')
            
        except Exception as e:
            print(f"❌ Error saving TIFF {filepath}: {e}")

def main():
    print("🔥 tCam-Mini Live Thermal Viewer")
    print("=" * 50)
    
    # Check if we should use AP mode or try to detect device
    import sys
    
    tcam_ip = "192.168.4.1"  # Default AP mode
    
    if len(sys.argv) > 1:
        tcam_ip = sys.argv[1]
        print(f"📡 Using custom IP: {tcam_ip}")
    else:
        print(f"📡 Using AP mode IP: {tcam_ip}")
        print("💡 Connect to tCam-Mini-CDE9 WiFi first!")
    
    viewer = LiveThermalViewer(tcam_ip)
    
    try:
        viewer.start_viewer()
    except KeyboardInterrupt:
        print("\n👋 Viewer stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
