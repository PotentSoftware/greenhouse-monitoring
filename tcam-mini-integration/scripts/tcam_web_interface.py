#!/usr/bin/env python3
"""
Simple Web Interface for tCam-Mini
Provides HTTP access to thermal images and device status
"""

from flask import Flask, render_template_string, jsonify, send_file
import socket
import json
import base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib.colors import LinearSegmentedColormap
import io
import threading
import time
from datetime import datetime
import cv2
import os

app = Flask(__name__)

class TcamWebInterface:
    def __init__(self, tcam_host='192.168.1.130', tcam_port=5001):
        self.tcam_host = tcam_host
        self.tcam_port = tcam_port
        self.latest_image = None
        self.device_info = {}
        self.stats = {}
        
        # Temperature conversion parameters for radiometric Lepton
        # Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
        self.LEPTON_RESOLUTION = 0.01  # Resolution: 0.01 K per raw unit
        
        # Create thermal colormap
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        self.thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
    
    def raw_to_celsius(self, raw_data):
        """Convert raw Lepton thermal data to Celsius
        Raw data is in Kelvin × 100, so conversion is: (raw × 0.01) - 273.15
        """
        celsius_data = (raw_data.astype(float) * self.LEPTON_RESOLUTION) - 273.15
        return celsius_data
        
    def connect_and_send(self, command):
        """Connect to tCam and send command"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.tcam_host, self.tcam_port))
            
            # Send command with delimiters
            cmd_json = json.dumps(command)
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
            response_str = response.decode().strip('\x02\x03')
            return json.loads(response_str)
            
        except Exception as e:
            print(f"Error communicating with tCam: {e}")
            return None
    
    def get_thermal_image(self):
        """Get thermal image from tCam"""
        data = self.connect_and_send({"cmd": "get_image"})
        if not data or 'radiometric' not in data:
            return None
            
        try:
            img_data = base64.b64decode(data['radiometric'])
            thermal_array = np.frombuffer(img_data, dtype=np.uint16)
            thermal_raw = thermal_array.reshape((120, 160))
            
            # Convert raw data to temperature in Celsius
            thermal_celsius = self.raw_to_celsius(thermal_raw)
            
            # Calculate temperature statistics in Celsius
            self.stats = {
                'min_temp': float(np.min(thermal_celsius)),
                'max_temp': float(np.max(thermal_celsius)),
                'avg_temp': float(np.mean(thermal_celsius)),
                'timestamp': datetime.now().isoformat()
            }
            
            # Store metadata
            if 'metadata' in data:
                self.device_info.update(data['metadata'])
            
            return thermal_celsius
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return None
    
    def get_device_status(self):
        """Get device status"""
        data = self.connect_and_send({"cmd": "get_status"})
        if data and 'status' in data:
            self.device_info.update(data['status'])
        return self.device_info
    
    def capture_video_frames(self, num_frames=10):
        """Capture multiple thermal frames for video creation"""
        frames = []
        print(f"Capturing {num_frames} thermal frames for video...")
        
        for i in range(num_frames):
            print(f"Capturing frame {i+1}/{num_frames}...")
            thermal_data = self.get_thermal_image()
            
            if thermal_data is not None:
                # Convert thermal data to 8-bit image for video
                # Normalize to 0-255 range
                normalized = ((thermal_data - thermal_data.min()) / 
                            (thermal_data.max() - thermal_data.min()) * 255).astype(np.uint8)
                
                # Apply thermal colormap
                colored_frame = plt.cm.get_cmap('hot')(normalized)
                # Convert to BGR format for OpenCV (remove alpha channel)
                bgr_frame = (colored_frame[:, :, :3] * 255).astype(np.uint8)
                bgr_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_RGB2BGR)
                
                frames.append(bgr_frame)
                
                # Small delay between frames
                time.sleep(0.2)
            else:
                print(f"Failed to capture frame {i+1}")
        
        return frames
    
    def create_video_file(self, frames, output_path):
        """Create video file from thermal frames"""
        if not frames:
            return False
            
        height, width = frames[0].shape[:2]
        
        # Define codec and create VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 2.0  # 2 frames per second for thermal video
        
        video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            print("Error: Could not open video writer")
            return False
        
        # Write frames to video
        for frame in frames:
            video_writer.write(frame)
        
        # Release video writer
        video_writer.release()
        print(f"Video saved to: {output_path}")
        return True

# Create global instance
tcam_interface = TcamWebInterface()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>tCam-Mini Web Interface</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        /* Dark theme matching greenhouse monitoring app */
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: #1a1a1a; 
            color: #e0e0e0;
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        .header { 
            background: linear-gradient(135deg, #2c3e50, #34495e); 
            color: #ffffff; 
            padding: 25px; 
            border-radius: 12px; 
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid #4caf50;
        }
        .header h1 {
            margin: 0;
            font-size: 2.2em;
            color: #4caf50;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        .header p {
            margin: 8px 0 0 0;
            opacity: 0.9;
            font-style: italic;
        }
        .content { 
            display: grid; 
            grid-template-columns: 2fr 1fr; 
            gap: 25px; 
        }
        .thermal-panel { 
            background: #2a2a2a; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid #404040;
        }
        .info-panel { 
            background: #2a2a2a; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 1px solid #404040;
        }
        .thermal-image { 
            max-width: 100%; 
            height: auto; 
            border: 2px solid #4caf50; 
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(76, 175, 80, 0.3);
        }
        .stats { 
            margin: 20px 0; 
        }
        .stat-item { 
            margin: 10px 0; 
            padding: 12px; 
            background: #333333; 
            border-radius: 6px;
            border-left: 4px solid #4caf50;
            transition: all 0.3s ease;
        }
        .stat-item:hover {
            background: #3a3a3a;
            transform: translateX(5px);
        }
        .controls { 
            margin: 25px 0; 
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .btn { 
            background: linear-gradient(135deg, #4caf50, #45a049); 
            color: white; 
            padding: 12px 20px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
        }
        .btn:hover { 
            background: linear-gradient(135deg, #45a049, #3d8b40);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .status-connected { 
            color: #4caf50; 
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        .status-error { 
            color: #f44336; 
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        .timestamp { 
            font-size: 0.9em; 
            color: #4caf50;
            font-style: italic;
            text-align: center;
            margin-top: 15px;
            padding: 8px;
            background: #333333;
            border-radius: 4px;
        }
        h2 {
            color: #4caf50;
            border-bottom: 2px solid #4caf50;
            padding-bottom: 8px;
            margin-bottom: 20px;
        }
        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #2a2a2a;
        }
        ::-webkit-scrollbar-thumb {
            background: #4caf50;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }
        /* Loading animation */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .loading {
            animation: pulse 1.5s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌡️ tCam-Mini Thermal Interface</h1>
            <p>Real-time thermal imaging for greenhouse monitoring</p>
            <div class="timestamp">Data acquired on: {{ timestamp }}</div>
        </div>
        
        <div class="content">
            <div class="thermal-panel">
                <h2>Live Thermal Image</h2>
                <img id="thermalImage" class="thermal-image" src="/thermal_image" alt="Thermal Image">
                <div class="controls">
                    <button class="btn" onclick="refreshImage()">🔄 Refresh Image</button>
                    <button class="btn" onclick="downloadImage()">💾 Download Image</button>
                    <button class="btn" onclick="captureVideo()" id="videoBtn">🎥 Capture Video (10 frames)</button>
                </div>
            </div>
            
            <div class="info-panel">
                <h2>Device Information</h2>
                <div id="deviceInfo">
                    <div class="stat-item">Loading device info...</div>
                </div>
                
                <h2>Temperature Statistics (°C)</h2>
                <div id="tempStats">
                    <div class="stat-item">Loading temperature data...</div>
                </div>
                
                <div class="controls">
                    <button class="btn" onclick="refreshStatus()">📊 Refresh Status</button>
                    <button class="btn" onclick="toggleAutoRefresh()">⏱️ Auto Refresh</button>
                </div>
                
                <div class="timestamp" id="lastUpdate">Last updated: Loading...</div>
            </div>
        </div>
    </div>

    <script>
        let autoRefresh = false;
        let refreshInterval;
        
        function refreshImage() {
            document.getElementById('thermalImage').src = '/thermal_image?' + new Date().getTime();
            refreshStatus();
        }
        
        function refreshStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    updateDeviceInfo(data.device);
                    updateTempStats(data.stats);
                    document.getElementById('lastUpdate').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('deviceInfo').innerHTML = '<div class="stat-item status-error">Connection Error</div>';
                });
        }
        
        function updateDeviceInfo(device) {
            const html = `
                <div class="stat-item"><strong>Camera:</strong> ${device.Camera || 'Unknown'}</div>
                <div class="stat-item"><strong>Model:</strong> ${device.Model || 'Unknown'}</div>
                <div class="stat-item"><strong>Version:</strong> ${device.Version || 'Unknown'}</div>
                <div class="stat-item status-connected"><strong>Status:</strong> Connected</div>
            `;
            document.getElementById('deviceInfo').innerHTML = html;
        }
        
        function updateTempStats(stats) {
            if (stats.min_temp !== undefined) {
                const html = `
                    <div class="stat-item"><strong>Min Temp:</strong> ${stats.min_temp.toFixed(1)}°C</div>
                    <div class="stat-item"><strong>Max Temp:</strong> ${stats.max_temp.toFixed(1)}°C</div>
                    <div class="stat-item"><strong>Avg Temp:</strong> ${stats.avg_temp.toFixed(1)}°C</div>
                    <div class="stat-item"><strong>Range:</strong> ${(stats.max_temp - stats.min_temp).toFixed(1)}°C</div>
                `;
                document.getElementById('tempStats').innerHTML = html;
            }
        }
        
        function downloadImage() {
            window.open('/thermal_image', '_blank');
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const btn = event.target;
            
            if (autoRefresh) {
                btn.textContent = '⏹️ Stop Auto';
                refreshInterval = setInterval(refreshImage, 2000);
            } else {
                btn.textContent = '⏱️ Auto Refresh';
                clearInterval(refreshInterval);
            }
        }
        
        function captureVideo() {
            const btn = document.getElementById('videoBtn');
            const originalText = btn.textContent;
            
            // Disable button and show progress
            btn.disabled = true;
            btn.textContent = '🎥 Capturing... (0/10)';
            
            // Start video capture
            fetch('/capture_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                } else {
                    throw new Error('Video capture failed');
                }
            })
            .then(blob => {
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `thermal_video_${new Date().toISOString().replace(/[:.]/g, '-')}.mp4`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                // Reset button
                btn.disabled = false;
                btn.textContent = originalText;
                
                alert('Video captured and downloaded successfully!');
            })
            .catch(error => {
                console.error('Error capturing video:', error);
                alert('Error capturing video: ' + error.message);
                
                // Reset button
                btn.disabled = false;
                btn.textContent = originalText;
            });
        }
        
        // Initial load
        refreshImage();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(HTML_TEMPLATE, timestamp=timestamp)

@app.route('/thermal_image')
def thermal_image():
    """Generate and serve thermal image"""
    thermal_data = tcam_interface.get_thermal_image()
    
    if thermal_data is None:
        # Return error image with dark theme
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#1a1a1a')
        ax.text(0.5, 0.5, 'No thermal data available', ha='center', va='center', 
                fontsize=16, color='#e0e0e0')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_facecolor('#2a2a2a')
    else:
        # Create thermal image with dark theme
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#1a1a1a')
        ax.set_facecolor('#2a2a2a')
        
        im = ax.imshow(thermal_data, cmap=tcam_interface.thermal_cmap, aspect='auto')
        
        # Dark theme styling
        title_text = f'🌡️ Thermal Image - {datetime.now().strftime("%H:%M:%S")} | Range: {thermal_data.min():.1f}°C to {thermal_data.max():.1f}°C'
        ax.set_title(title_text, color='#4caf50', fontsize=12, fontweight='bold', pad=20)
        ax.set_xlabel('Pixel X', color='#e0e0e0')
        ax.set_ylabel('Pixel Y', color='#e0e0e0')
        
        # Style tick labels
        ax.tick_params(colors='#e0e0e0')
        
        # Add colorbar with dark theme
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Temperature (°C)', color='#e0e0e0', fontweight='bold')
        cbar.ax.tick_params(colors='#e0e0e0')
        
        # Style the figure
        fig.patch.set_facecolor('#1a1a1a')
    
    # Save to BytesIO
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)
    plt.close(fig)
    
    return send_file(img_buffer, mimetype='image/png')

@app.route('/status')
def status():
    """Get device status and temperature stats"""
    device_info = tcam_interface.get_device_status()
    return jsonify({
        'device': device_info,
        'stats': tcam_interface.stats
    })

@app.route('/capture_video', methods=['POST'])
def capture_video():
    """Capture thermal video and return as downloadable file"""
    try:
        # Capture frames
        frames = tcam_interface.capture_video_frames(num_frames=10)
        
        if not frames:
            return jsonify({'error': 'Failed to capture frames'}), 500
        
        # Create temporary video file
        desktop_path = os.path.expanduser('~/Desktop')
        if not os.path.exists(desktop_path):
            desktop_path = os.path.expanduser('~')  # Fallback to home directory
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_filename = f'thermal_video_{timestamp}.mp4'
        video_path = os.path.join(desktop_path, video_filename)
        
        # Create video file
        success = tcam_interface.create_video_file(frames, video_path)
        
        if success and os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name=video_filename, mimetype='video/mp4')
        else:
            return jsonify({'error': 'Failed to create video file'}), 500
            
    except Exception as e:
        print(f"Error in video capture: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Starting tCam-Mini Web Interface...")
    print("📱 Access at: http://localhost:8080")
    print("🌡️  Connecting to tCam-Mini at 192.168.1.130:5001")
    app.run(host='0.0.0.0', port=8080, debug=False)
