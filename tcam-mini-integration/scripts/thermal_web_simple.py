#!/usr/bin/env python3
"""
Simple Robust Thermal Web Viewer - Auto-detects tCam-Mini or uses demo mode
"""

from flask import Flask, jsonify, send_file, request
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import threading
import time
from PIL import Image
import io
from pathlib import Path
import random
import argparse

class SimpleRobustViewer:
    def __init__(self, tcam_ip="192.168.1.223"):
        self.tcam_ip = tcam_ip
        self.base_url = None
        self.mode = "demo"  # demo or connected
        self.current_analysis = None
        self.current_image_path = None
        self.lock = threading.Lock()
        self.output_dir = Path("thermal_simple")
        
        # Configurable segmentation parameters
        self.params = {
            'threshold_multiplier': 1.5,  # Multiplier for background + X * std
            'threshold_method': 'median',  # 'median' or 'mean'
            'kernel_size': 3,  # Morphological kernel size
            'min_area': 30,    # Minimum region area
            'max_area': 1500,  # Maximum region area
            'morph_open_iterations': 1,
            'morph_close_iterations': 1
        }
        self.output_dir.mkdir(exist_ok=True)
        
        # Try to find tCam-Mini
        self._detect_tcam()
    
    def _detect_tcam(self):
        """Try to find tCam-Mini on common ports"""
        print("🔍 Searching for tCam-Mini...")
        for port in [8080, 8081, 5000, 3000]:
            try:
                url = f"http://{self.tcam_ip}:{port}"
                resp = requests.get(f"{url}/status", timeout=2)
                if resp.status_code == 200 and ('device' in resp.text or 'stats' in resp.text):
                    self.base_url = url
                    self.mode = "connected"
                    print(f"✅ Found tCam-Mini at {url}")
                    return
            except:
                continue
        print("❌ tCam-Mini not found, using demo mode")
    
    def start_analysis(self):
        """Start background analysis thread"""
        def loop():
            while True:
                try:
                    if self.mode == "connected":
                        data, info = self._get_real_data()
                    else:
                        data, info = self._get_demo_data()
                    
                    if data is not None:
                        results = self._analyze(data)
                        img_path = self.output_dir / f"thermal_{datetime.now().strftime('%H%M%S')}.png"
                        self._create_viz(data, results, img_path)
                        
                        with self.lock:
                            self.current_analysis = {
                                'timestamp': datetime.now().isoformat(),
                                'mode': self.mode,
                                'regions': len(results['regions']),
                                'temp_range': f"{np.min(data):.1f}-{np.max(data):.1f}°C",
                                'results': results
                            }
                            self.current_image_path = str(img_path)
                        
                        print(f"✅ Analysis: {len(results['regions'])} regions ({self.mode})")
                except Exception as e:
                    print(f"❌ Error: {e}")
                
                time.sleep(3)
        
        threading.Thread(target=loop, daemon=True).start()
        print("🚀 Analysis started")
    
    def _get_real_data(self):
        """Get data from real tCam-Mini"""
        try:
            # Get status
            status_resp = requests.get(f"{self.base_url}/status", timeout=5)
            device_info = status_resp.json()
            
            # Get thermal image
            img_resp = requests.get(f"{self.base_url}/thermal_image", timeout=5)
            img_data = Image.open(io.BytesIO(img_resp.content))
            img_array = np.array(img_data)
            
            # Convert to temperature
            if len(img_array.shape) == 3:
                thermal_data = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY).astype(np.float32)
                # Use default temperature range if not available in device stats
                min_temp = device_info.get('stats', {}).get('min_temp', 15.0)
                max_temp = device_info.get('stats', {}).get('max_temp', 35.0)
                thermal_data = min_temp + (thermal_data / 255.0) * (max_temp - min_temp)
            else:
                thermal_data = img_array.astype(np.float32)
            
            return thermal_data, device_info
        except Exception as e:
            print(f"❌ Real data failed: {e}")
            # Switch to demo mode
            self.mode = "demo"
            return None, None
    
    def _get_demo_data(self):
        """Generate simulated thermal data"""
        # Create 120x160 base image
        thermal_data = np.full((120, 160), 20.0 + random.uniform(-2, 2), dtype=np.float32)
        
        # Add noise
        thermal_data += np.random.normal(0, 0.5, (120, 160))
        
        # Add hot spots
        for _ in range(random.randint(3, 8)):
            cx, cy = random.randint(20, 140), random.randint(20, 100)
            radius = random.randint(8, 25)
            temp_inc = random.uniform(3, 10)
            
            # Create distance map
            y_coords, x_coords = np.meshgrid(range(160), range(120), indexing='xy')
            distance = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
            mask = distance <= radius
            thermal_data[mask] += temp_inc * np.exp(-(distance[mask]**2) / (2 * (radius/3)**2))
        
        # Scale up
        thermal_data = cv2.resize(thermal_data, (640, 480), interpolation=cv2.INTER_LINEAR)
        
        device_info = {
            'device': {'Camera': 'Demo', 'Version': '1.0'},
            'stats': {'min_temp': float(np.min(thermal_data)), 'max_temp': float(np.max(thermal_data))}
        }
        
        return thermal_data, device_info
    
    def _analyze(self, thermal_data):
        """Configurable thermal analysis"""
        # Threshold using configurable parameters
        if self.params['threshold_method'] == 'median':
            bg_temp = np.median(thermal_data)
        else:
            bg_temp = np.mean(thermal_data)
        
        threshold = bg_temp + self.params['threshold_multiplier']
        binary_mask = thermal_data > threshold
        
        # Morphology with configurable kernel
        kernel_size = self.params['kernel_size']
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        # Apply morphological operations with configurable iterations
        cleaned = binary_mask.astype(np.uint8)
        for _ in range(self.params['morph_open_iterations']):
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        for _ in range(self.params['morph_close_iterations']):
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
        
        # Connected components
        num_labels, labeled = cv2.connectedComponents(cleaned)
        
        # Extract regions with configurable area limits
        regions = []
        for label in range(1, num_labels):
            mask = (labeled == label)
            area = np.sum(mask)
            if self.params['min_area'] <= area <= self.params['max_area']:
                temps = thermal_data[mask]
                y_coords, x_coords = np.where(mask)
                regions.append({
                    'id': int(label),
                    'area': int(area),
                    'mean_temp': float(np.mean(temps)),
                    'centroid': (float(np.mean(x_coords)), float(np.mean(y_coords)))
                })
        
        return {
            'regions': regions,
            'debug': {'binary_mask': binary_mask, 'cleaned': cleaned, 'labeled': labeled}
        }
    
    def _create_viz(self, thermal_data, results, save_path):
        """Create extra large, detailed visualization for parameter tuning"""
        fig, axes = plt.subplots(2, 3, figsize=(32, 20))  # Much larger figure
        fig.suptitle(f'Thermal Analysis ({self.mode}) - {datetime.now().strftime("%H:%M:%S")}', fontsize=24, y=0.98)
        
        # Row 1: Original images
        # Original thermal image (unprocessed)
        im1 = axes[0, 0].imshow(thermal_data, cmap='hot', interpolation='nearest')
        axes[0, 0].set_title('Original Thermal Image\n(Unprocessed)', fontsize=18, fontweight='bold', pad=25)
        cbar1 = plt.colorbar(im1, ax=axes[0, 0], shrink=0.8, label='Temperature (°C)')
        cbar1.ax.tick_params(labelsize=14)
        cbar1.set_label('Temperature (°C)', fontsize=14)
        
        # Thermal with temperature scale
        im2 = axes[0, 1].imshow(thermal_data, cmap='inferno', interpolation='nearest')
        axes[0, 1].set_title('Thermal Image\n(Enhanced Colormap)', fontsize=18, fontweight='bold', pad=25)
        cbar2 = plt.colorbar(im2, ax=axes[0, 1], shrink=0.8, label='Temperature (°C)')
        cbar2.ax.tick_params(labelsize=14)
        cbar2.set_label('Temperature (°C)', fontsize=14)
        
        # Threshold mask
        axes[0, 2].imshow(results['debug']['binary_mask'], cmap='gray')
        axes[0, 2].set_title('Temperature Threshold\n(Hot Regions)', fontsize=18, fontweight='bold', pad=25)
        
        # Row 2: Processed images
        # Cleaned mask
        axes[1, 0].imshow(results['debug']['cleaned'], cmap='gray')
        axes[1, 0].set_title('Cleaned Mask\n(Noise Filtered)', fontsize=18, fontweight='bold', pad=25)
        
        # Segmented regions with overlay
        overlay = self._create_overlay(thermal_data, results['regions'], results['debug']['labeled'])
        axes[1, 1].imshow(overlay)
        axes[1, 1].set_title(f'Segmented Regions\n({len(results["regions"])} detected)', fontsize=18, fontweight='bold', pad=25)
        
        # Statistics panel
        self._create_stats_panel(axes[1, 2], thermal_data, results['regions'])
        
        # Add labels for regions (show more with much larger text)
        for region in results['regions'][:25]:  # Show even more regions
            cx, cy = region['centroid']
            axes[1, 1].text(cx, cy, f"R{region['id']}", color='yellow', fontsize=16, 
                           ha='center', va='center', fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.9))
        
        plt.tight_layout(pad=2.0)  # More padding
        plt.savefig(save_path, dpi=150, bbox_inches='tight')  # Higher DPI
        plt.close()
    
    def _create_stats_panel(self, ax, thermal_data, regions):
        """Create statistics panel"""
        ax.axis('off')
        ax.set_title('Analysis Statistics', fontsize=12, fontweight='bold')
        
        # Calculate statistics
        temp_min = float(np.min(thermal_data))
        temp_max = float(np.max(thermal_data))
        temp_mean = float(np.mean(thermal_data))
        temp_std = float(np.std(thermal_data))
        
        # Region statistics
        if regions:
            region_temps = [r['mean_temp'] for r in regions]
            region_areas = [r['area'] for r in regions]
            hottest_temp = max(region_temps)
            largest_area = max(region_areas)
        else:
            hottest_temp = temp_max
            largest_area = 0
        
        # Create text
        stats_text = f"""TEMPERATURE RANGE:
Min: {temp_min:.1f}°C
Max: {temp_max:.1f}°C
Mean: {temp_mean:.1f}°C
Std: {temp_std:.1f}°C

REGION ANALYSIS:
Regions: {len(regions)}
Hottest: {hottest_temp:.1f}°C
Largest: {largest_area} px

COVERAGE:
Total pixels: {thermal_data.size}
Hot pixels: {sum(region_areas) if regions else 0}
Coverage: {(sum(region_areas)/thermal_data.size*100) if regions else 0:.1f}%"""
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='lightgray', alpha=0.8))
    
    def _create_overlay(self, thermal_data, regions, labeled):
        """Create colored region overlay"""
        from matplotlib.colors import Normalize
        from matplotlib.cm import hot
        
        norm = Normalize(vmin=np.percentile(thermal_data, 5), vmax=np.percentile(thermal_data, 95))
        rgb_image = hot(norm(thermal_data))
        
        if len(regions) > 0:
            colors = plt.cm.Set3(np.linspace(0, 1, len(regions)))
            for i, region in enumerate(regions):
                mask = (labeled == region['id'])
                if np.any(mask):
                    color = colors[i % len(colors)]
                    for c in range(3):
                        rgb_image[mask, c] = 0.5 * rgb_image[mask, c] + 0.5 * color[c]
        
        return rgb_image

# Flask App
app = Flask(__name__)
viewer = None

@app.route('/')
def index():
    return '''<!DOCTYPE html>
<html><head><title>Simple Thermal Viewer</title>
<style>
body{font-family:Arial;background:#1a1a1a;color:#e0e0e0;padding:10px;margin:0;}
.container{max-width:1800px;margin:0 auto;}
.header{background:#2c3e50;padding:15px;border-radius:8px;margin-bottom:15px;border:1px solid #4caf50;}
.header h1{margin:0;color:#4caf50;font-size:1.5em;}
.content{display:grid;grid-template-columns:1fr 350px;gap:15px;height:calc(100vh - 120px);}
.main-panel{background:#2a2a2a;padding:15px;border-radius:8px;border:1px solid #444;overflow:auto;}
.control-panel{background:#2a2a2a;padding:15px;border-radius:8px;border:1px solid #444;overflow-y:auto;}
.thermal-image{max-width:none;width:auto;height:auto;border:2px solid #4caf50;border-radius:4px;display:block;}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:15px;}
.stat{background:#333;padding:10px;border-radius:4px;border-left:3px solid #4caf50;}
.stat-label{font-size:0.9em;color:#aaa;}
.stat-value{font-size:1.1em;font-weight:bold;color:#4caf50;}
.status{padding:10px;border-radius:4px;margin:10px 0;text-align:center;font-weight:bold;}
.status.connected{background:#2d5a2d;color:#4caf50;border:1px solid #4caf50;}
.status.demo{background:#5a4d2d;color:#ff9800;border:1px solid #ff9800;}
.params{margin-top:15px;}
.param{margin:10px 0;}
.param label{display:block;margin-bottom:5px;color:#e0e0e0;font-size:0.9em;}
.param input[type="range"]{width:100%;height:6px;border-radius:3px;background:#444;outline:none;}
.param input[type="range"]::-webkit-slider-thumb{appearance:none;width:16px;height:16px;border-radius:50%;background:#4caf50;cursor:pointer;}
.param input[type="range"]::-moz-range-thumb{width:16px;height:16px;border-radius:50%;background:#4caf50;cursor:pointer;border:none;}
</style></head><body>
<div class="container">
<div class="header"><h1>🌡️ Simple Thermal Viewer</h1><p>Auto-detecting tCam-Mini with demo fallback</p></div>
<div class="content">
<div class="main-panel">
<h2 style="margin:0 0 15px 0;color:#4caf50;">🔥 Live Thermal Analysis</h2>
<img id="img" class="thermal-image" src="/image" alt="Loading...">
<div style="text-align:center;color:#888;margin-top:15px;font-size:1.1em;">
<span id="update">Loading...</span> | Auto-refresh every 3 seconds
</div></div>
<div class="control-panel">
<h3 style="margin:0 0 15px 0;">📊 Status</h3>
<div id="status" class="status">Initializing...</div>
<div class="stats" id="stats"></div>
<h3 style="margin:20px 0 15px 0;">🎛️ Parameters</h3>
<div class="params">
<div class="param">
<label>Threshold Multiplier: <span id="threshold-val">1.5</span></label>
<input type="range" id="threshold" min="0.5" max="3.0" step="0.1" value="1.5">
</div>
<div class="param">
<label>Kernel Size: <span id="kernel-val">3</span></label>
<input type="range" id="kernel" min="1" max="7" step="2" value="3">
</div>
<div class="param">
<label>Min Area: <span id="minarea-val">30</span></label>
<input type="range" id="minarea" min="10" max="100" step="5" value="30">
</div>
<div class="param">
<label>Max Area: <span id="maxarea-val">1500</span></label>
<input type="range" id="maxarea" min="500" max="3000" step="50" value="1500">
</div>
<button id="reset-params" style="background:#ff6b6b;color:white;border:none;padding:8px 16px;border-radius:4px;margin-top:10px;cursor:pointer;">Reset to Defaults</button>
</div>
</div></div></div>
<script>
function update(){
fetch('/api').then(r=>r.json()).then(d=>{
if(d.status==='ok'){
document.getElementById('img').src='/image?'+Date.now();
document.getElementById('update').textContent='Updated: '+new Date(d.timestamp).toLocaleTimeString();
const st=document.getElementById('status');
if(d.mode==='connected'){st.className='status connected';st.textContent='✅ Connected to tCam-Mini';}
else{st.className='status demo';st.textContent='🎭 Demo Mode';}
const stats=document.getElementById('stats');
stats.innerHTML=`
<div class="stat"><div class="stat-label">Mode</div><div class="stat-value">${d.mode}</div></div>
<div class="stat"><div class="stat-label">Regions</div><div class="stat-value">${d.regions}</div></div>
<div class="stat"><div class="stat-label">Temperature</div><div class="stat-value">${d.temp_range}</div></div>
<div class="stat"><div class="stat-label">Last Update</div><div class="stat-value">${new Date(d.timestamp).toLocaleTimeString()}</div></div>
`;}}).catch(e=>console.error(e));}

// Parameter controls
function setupParams(){
const params=['threshold','kernel','minarea','maxarea'];
params.forEach(p=>{
const slider=document.getElementById(p);
const display=document.getElementById(p+'-val');
slider.addEventListener('input',()=>{
display.textContent=slider.value;
updateParam(p,slider.value);
});
});
document.getElementById('reset-params').addEventListener('click',()=>{
fetch('/reset_params',{method:'POST'}).then(()=>location.reload());
});
}

function updateParam(name,value){
fetch('/update_param',{
method:'POST',
headers:{'Content-Type':'application/json'},
body:JSON.stringify({param:name,value:parseFloat(value)})
}).catch(e=>console.error(e));
}

update();setInterval(update,3000);setupParams();
</script></body></html>'''

@app.route('/api')
def api():
    with viewer.lock:
        if viewer.current_analysis:
            return jsonify({
                'status': 'ok',
                'timestamp': viewer.current_analysis['timestamp'],
                'mode': viewer.current_analysis['mode'],
                'regions': viewer.current_analysis['regions'],
                'temp_range': viewer.current_analysis['temp_range']
            })
        else:
            return jsonify({'status': 'no_data'})

@app.route('/image')
def image():
    with viewer.lock:
        if viewer.current_image_path and Path(viewer.current_image_path).exists():
            return send_file(viewer.current_image_path, mimetype='image/png')
        else:
            # Placeholder
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, 'Loading...', ha='center', va='center', transform=ax.transAxes, fontsize=16)
            ax.axis('off')
            temp_path = viewer.output_dir / "placeholder.png"
            plt.savefig(temp_path, bbox_inches='tight')
            plt.close()
            return send_file(temp_path, mimetype='image/png')

@app.route('/update_param', methods=['POST'])
def update_param():
    data = request.get_json()
    param_name = data.get('param')
    param_value = data.get('value')
    
    # Map frontend names to backend parameter names
    param_map = {
        'threshold': 'threshold_multiplier',
        'kernel': 'kernel_size',
        'minarea': 'min_area',
        'maxarea': 'max_area'
    }
    
    if param_name in param_map:
        backend_name = param_map[param_name]
        with viewer.lock:
            viewer.params[backend_name] = param_value
        print(f"🎛️ Updated {backend_name}: {param_value}")
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid parameter'}), 400

@app.route('/reset_params', methods=['POST'])
def reset_params():
    with viewer.lock:
        viewer.params = {
            'threshold_multiplier': 1.5,
            'threshold_method': 'median',
            'kernel_size': 3,
            'min_area': 30,
            'max_area': 1500,
            'morph_open_iterations': 1,
            'morph_close_iterations': 1
        }
    print("🔄 Reset parameters to defaults")
    return jsonify({'status': 'ok'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tcam-ip', default='192.168.1.223', help='tCam-Mini IP')
    parser.add_argument('--port', type=int, default=5002, help='Web port')
    args = parser.parse_args()
    
    global viewer
    viewer = SimpleRobustViewer(args.tcam_ip)
    viewer.start_analysis()
    
    print(f"🌐 Starting web interface on http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
