#!/usr/bin/env python3
"""
Raw Thermal Image Viewer for tCam-Mini
Shows unprocessed thermal images directly from the camera
"""

from flask import Flask, render_template_string, jsonify, Response
import requests
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import time
from datetime import datetime
import cv2

app = Flask(__name__)

class RawThermalViewer:
    def __init__(self, tcam_ip="192.168.4.1"):
        self.tcam_ip = tcam_ip
        self.base_url = None
        self.latest_image = None
        self.status = "Searching for device..."
        
        # Try to find the device
        self._find_device()
    
    def _find_device(self):
        """Find tCam-Mini device"""
        print(f"🔍 Looking for tCam-Mini at {self.tcam_ip}...")
        
        # Try common ports
        for port in [80, 5001, 8080]:
            try:
                url = f"http://{self.tcam_ip}:{port}"
                print(f"Testing {url}...")
                
                # Test status endpoint
                response = requests.get(f"{url}/status", timeout=3)
                if response.status_code == 200:
                    self.base_url = url
                    self.status = f"Connected to {url}"
                    print(f"✅ Found tCam-Mini at {url}")
                    return
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Failed to connect to {url}: {e}")
                continue
        
        self.status = f"❌ tCam-Mini not found at {self.tcam_ip}"
        print(self.status)
    
    def get_thermal_image(self):
        """Get raw thermal image from tCam-Mini"""
        if not self.base_url:
            return None
            
        try:
            # Try different thermal endpoints
            endpoints = ['/thermal_raw', '/thermal', '/image', '/lepton']
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        print(f"✅ Got thermal data from {endpoint}")
                        
                        # Handle different response types
                        if response.headers.get('content-type', '').startswith('image/'):
                            # Direct image response
                            return response.content
                        else:
                            # JSON response with image data
                            try:
                                data = response.json()
                                if 'thermal_pixels' in data:
                                    return self._convert_pixels_to_image(data['thermal_pixels'])
                                elif 'image' in data:
                                    return base64.b64decode(data['image'])
                            except:
                                pass
                                
                except requests.exceptions.RequestException:
                    continue
                    
        except Exception as e:
            print(f"❌ Error getting thermal image: {e}")
            
        return None
    
    def _convert_pixels_to_image(self, pixels):
        """Convert thermal pixel array to image"""
        try:
            # Convert to numpy array
            if isinstance(pixels, list):
                thermal_array = np.array(pixels, dtype=np.float32)
            else:
                thermal_array = np.array(pixels, dtype=np.float32)
            
            # Reshape to 80x60 (Lepton 3.5 resolution)
            if thermal_array.size == 4800:  # 80x60
                thermal_array = thermal_array.reshape(60, 80)
            elif thermal_array.size == 19200:  # 160x120
                thermal_array = thermal_array.reshape(120, 160)
            
            # Normalize to 0-255
            thermal_norm = ((thermal_array - thermal_array.min()) / 
                           (thermal_array.max() - thermal_array.min()) * 255).astype(np.uint8)
            
            # Apply colormap
            plt.figure(figsize=(8, 6))
            plt.imshow(thermal_norm, cmap='hot', interpolation='nearest')
            plt.colorbar(label='Temperature (relative)')
            plt.title(f'Raw Thermal Image - {datetime.now().strftime("%H:%M:%S")}')
            plt.axis('off')
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error converting pixels: {e}")
            return None

# Global viewer instance
viewer = RawThermalViewer()

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raw Thermal Camera Viewer</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .disconnected { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .image-container { text-align: center; margin: 20px 0; }
            .thermal-image { max-width: 100%; height: auto; border: 2px solid #ddd; border-radius: 5px; }
            .info { background: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌡️ Raw Thermal Camera Viewer</h1>
            
            <div class="status {{ 'connected' if viewer.base_url else 'disconnected' }}">
                <strong>Status:</strong> {{ viewer.status }}
            </div>
            
            {% if viewer.base_url %}
            <div class="info">
                <strong>Device:</strong> {{ viewer.base_url }}<br>
                <strong>Mode:</strong> Raw thermal imaging (no processing)<br>
                <strong>Refresh:</strong> Auto-refresh every 2 seconds
            </div>
            
            <div class="image-container">
                <img src="/thermal_image" class="thermal-image" alt="Thermal Image">
            </div>
            {% else %}
            <div class="info">
                <strong>Troubleshooting:</strong><br>
                • Check tCam-Mini is powered on<br>
                • Verify device IP: {{ viewer.tcam_ip }}<br>
                • Ensure device is connected to WiFi<br>
                • Wait for Lepton sensor to initialize
            </div>
            {% endif %}
            
            <div class="info">
                <strong>Last Update:</strong> {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, viewer=viewer, datetime=datetime)

@app.route('/thermal_image')
def thermal_image():
    """Serve the latest thermal image"""
    image_data = viewer.get_thermal_image()
    
    if image_data:
        return Response(image_data, mimetype='image/png')
    else:
        # Return a placeholder image
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, 'No Thermal Data\nAvailable', 
                ha='center', va='center', fontsize=20, color='red')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis('off')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return Response(img_buffer.getvalue(), mimetype='image/png')

@app.route('/status')
def status():
    """Device status endpoint"""
    return jsonify({
        'device_ip': viewer.tcam_ip,
        'base_url': viewer.base_url,
        'status': viewer.status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🌡️ Starting Raw Thermal Viewer...")
    print(f"📱 Access at: http://localhost:8081")
    print(f"🎯 Target device: {viewer.tcam_ip}")
    
    app.run(host='0.0.0.0', port=8081, debug=False)
