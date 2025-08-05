#!/usr/bin/env python3
"""
GUI Thermal Capture Tool for tCam-Mini
Simple GUI with button to capture 10 sequential images in all formats
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
from datetime import datetime
import socket
import json
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for threading
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

class ThermalCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("tCam-Mini Thermal Capture Tool")
        self.root.geometry("600x500")
        
        # Configuration
        self.tcam_ip = tk.StringVar(value="192.168.1.130")
        self.tcam_port = tk.IntVar(value=5001)
        self.num_images = tk.IntVar(value=10)
        self.desktop_path = os.path.expanduser("~/Desktop")
        
        # Ensure Desktop exists
        if not os.path.exists(self.desktop_path):
            os.makedirs(self.desktop_path)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Title
        title_label = tk.Label(self.root, text="🌡️ tCam-Mini Thermal Capture", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        # IP Address
        ttk.Label(config_frame, text="tCam-Mini IP:").grid(row=0, column=0, sticky="w", padx=5)
        ip_entry = ttk.Entry(config_frame, textvariable=self.tcam_ip, width=15)
        ip_entry.grid(row=0, column=1, padx=5)
        
        # Port
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, sticky="w", padx=5)
        port_entry = ttk.Entry(config_frame, textvariable=self.tcam_port, width=8)
        port_entry.grid(row=0, column=3, padx=5)
        
        # Number of images
        ttk.Label(config_frame, text="Images to capture:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        num_spinbox = ttk.Spinbox(config_frame, from_=1, to=50, textvariable=self.num_images, width=8)
        num_spinbox.grid(row=1, column=1, padx=5, pady=5)
        
        # Output path
        ttk.Label(config_frame, text="Output folder:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(config_frame, text="~/Desktop", foreground="blue").grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=20)
        
        # Test connection button
        self.test_btn = tk.Button(buttons_frame, text="🔍 Test Connection", 
                                 command=self.test_connection, bg="#e3f2fd", width=15)
        self.test_btn.pack(side="left", padx=5)
        
        # Single capture button
        self.single_btn = tk.Button(buttons_frame, text="📷 Single Capture", 
                                   command=self.single_capture, bg="#f3e5f5", width=15)
        self.single_btn.pack(side="left", padx=5)
        
        # Multi capture button (the main one you wanted)
        self.multi_btn = tk.Button(buttons_frame, text="🎯 Capture 10 Images", 
                                  command=self.multi_capture, bg="#e8f5e8", 
                                  width=20, height=2, font=("Arial", 12, "bold"))
        self.multi_btn.pack(side="left", padx=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=10)
        
        # Status text area
        status_frame = ttk.LabelFrame(self.root, text="Status Log", padding=5)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=15, width=70)
        self.status_text.pack(fill="both", expand=True)
        
        # Initial status
        self.log("🚀 Thermal Capture Tool Ready")
        self.log(f"📁 Output folder: {self.desktop_path}")
        self.log("💡 Click 'Test Connection' to verify tCam-Mini connectivity")
        
    def log(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update()
        
    def get_thermal_data(self):
        """Get thermal data from tCam-Mini"""
        try:
            ip = self.tcam_ip.get()
            port = self.tcam_port.get()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            sock.connect((ip, port))
            
            command = b'\x02{"cmd": "get_image"}\x03'
            sock.send(command)
            
            # Receive response in chunks to handle large thermal data
            response = b''
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    response += chunk
                    if response.endswith(b'\x03'):
                        break
                except socket.timeout:
                    break
            
            sock.close()
            
            if not response:
                self.log("❌ No response received from tCam-Mini")
                return None, None
                
            if response.startswith(b'\x02') and response.endswith(b'\x03'):
                response = response[1:-1]
            else:
                self.log(f"❌ Invalid response format. Length: {len(response)}")
                self.log(f"❌ First 100 chars: {response[:100]}")
                return None, None
            
            try:
                data = json.loads(response.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.log(f"❌ JSON decode error: {e}")
                self.log(f"❌ Response length: {len(response)}")
                self.log(f"❌ Response preview: {response[:200]}")
                return None, None
            
            if 'radiometric' not in data:
                return None, None
            
            thermal_data = base64.b64decode(data['radiometric'])
            thermal_array = np.frombuffer(thermal_data, dtype=np.uint16)
            thermal_array = thermal_array.reshape((120, 160))
            temp_celsius = (thermal_array * 0.01) - 273.15
            
            return thermal_array, temp_celsius
            
        except Exception as e:
            self.log(f"❌ Error getting thermal data: {e}")
            return None, None
    
    def save_thermal_formats(self, raw_data, temp_celsius, base_filename):
        """Save thermal data in all three formats"""
        try:
            # 1. Save as .npy
            npy_path = os.path.join(self.desktop_path, f"{base_filename}.npy")
            np.save(npy_path, temp_celsius)
            
            # 2. Save as .tiff
            tiff_path = os.path.join(self.desktop_path, f"{base_filename}.tiff")
            temp_int16 = (temp_celsius * 100).astype(np.int16)
            Image.fromarray(temp_int16, mode='I;16').save(tiff_path)
            
            # 3. Save as .png
            png_path = os.path.join(self.desktop_path, f"{base_filename}.png")
            
            colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                     '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
            thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
            
            plt.figure(figsize=(8, 6))
            plt.imshow(temp_celsius, cmap=thermal_cmap, aspect='equal')
            plt.colorbar(label='Temperature (°C)')
            plt.title(f'Thermal Image - {base_filename}')
            
            min_temp = temp_celsius.min()
            max_temp = temp_celsius.max()
            mean_temp = temp_celsius.mean()
            
            plt.text(0.02, 0.98, f'Min: {min_temp:.1f}°C\nMax: {max_temp:.1f}°C\nMean: {mean_temp:.1f}°C', 
                     transform=plt.gca().transAxes, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(png_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return True, (min_temp, max_temp, mean_temp)
            
        except Exception as e:
            self.log(f"❌ Error saving files: {e}")
            return False, None
    
    def test_connection(self):
        """Test connection to tCam-Mini"""
        def test_thread():
            self.test_btn.config(state="disabled")
            self.log("🔍 Testing connection to tCam-Mini...")
            
            try:
                ip = self.tcam_ip.get()
                port = self.tcam_port.get()
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((ip, port))
                
                command = b'\x02{"cmd": "get_status"}\x03'
                sock.send(command)
                response = sock.recv(1024)
                sock.close()
                
                if response.startswith(b'\x02') and response.endswith(b'\x03'):
                    response = response[1:-1]
                    data = json.loads(response.decode('utf-8'))
                    
                    if 'status' in data:
                        camera = data['status'].get('Camera', 'Unknown')
                        version = data['status'].get('Version', 'Unknown')
                        self.log(f"✅ Connection successful!")
                        self.log(f"📷 Device: {camera} v{version}")
                    else:
                        self.log("⚠️ Connected but unexpected response")
                else:
                    self.log("⚠️ Connected but invalid response format")
                    
            except Exception as e:
                self.log(f"❌ Connection failed: {e}")
                self.log("💡 Try power cycling the tCam-Mini or check IP address")
            
            self.test_btn.config(state="normal")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def single_capture(self):
        """Capture a single thermal image"""
        def capture_thread():
            self.single_btn.config(state="disabled")
            self.log("📷 Capturing single thermal image...")
            
            raw_data, temp_celsius = self.get_thermal_data()
            
            if raw_data is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"thermal_single_{timestamp}"
                
                success, stats = self.save_thermal_formats(raw_data, temp_celsius, base_filename)
                
                if success:
                    min_temp, max_temp, mean_temp = stats
                    self.log(f"✅ Single capture successful!")
                    self.log(f"🌡️ Temperature: {min_temp:.1f}°C - {max_temp:.1f}°C (avg: {mean_temp:.1f}°C)")
                    self.log(f"💾 Saved: {base_filename}.[npy|tiff|png]")
                else:
                    self.log("❌ Failed to save thermal image")
            else:
                self.log("❌ Failed to capture thermal image")
            
            self.single_btn.config(state="normal")
        
        threading.Thread(target=capture_thread, daemon=True).start()
    
    def multi_capture(self):
        """Capture multiple thermal images - THE MAIN FEATURE YOU WANTED"""
        def capture_thread():
            self.multi_btn.config(state="disabled")
            num_images = self.num_images.get()
            
            self.log(f"🎯 Starting capture of {num_images} thermal images...")
            self.log("📁 Saving in .npy, .tiff, and .png formats to ~/Desktop")
            
            self.progress['maximum'] = num_images
            self.progress['value'] = 0
            
            session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            successful = 0
            failed = 0
            
            for i in range(1, num_images + 1):
                self.log(f"📷 Capturing image {i}/{num_images}...")
                
                raw_data, temp_celsius = self.get_thermal_data()
                
                if raw_data is not None:
                    base_filename = f"thermal_{session_timestamp}_{i:02d}"
                    success, stats = self.save_thermal_formats(raw_data, temp_celsius, base_filename)
                    
                    if success:
                        min_temp, max_temp, mean_temp = stats
                        self.log(f"✅ Image {i} saved! ({min_temp:.1f}°C - {max_temp:.1f}°C)")
                        successful += 1
                    else:
                        self.log(f"❌ Failed to save image {i}")
                        failed += 1
                else:
                    self.log(f"❌ Failed to capture image {i}")
                    failed += 1
                
                self.progress['value'] = i
                
                if i < num_images:
                    import time
                    time.sleep(0.5)  # Brief pause between captures
            
            # Summary
            self.log("=" * 50)
            self.log(f"📊 CAPTURE COMPLETE!")
            self.log(f"✅ Successful: {successful}")
            self.log(f"❌ Failed: {failed}")
            
            if successful > 0:
                self.log(f"📁 Files saved to: {self.desktop_path}")
                self.log(f"🏷️ Pattern: thermal_{session_timestamp}_XX.[npy|tiff|png]")
                messagebox.showinfo("Capture Complete", 
                                  f"Successfully captured {successful} thermal images!\n"
                                  f"Files saved to ~/Desktop")
            
            self.progress['value'] = 0
            self.multi_btn.config(state="normal")
        
        threading.Thread(target=capture_thread, daemon=True).start()

def main():
    root = tk.Tk()
    app = ThermalCaptureGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
