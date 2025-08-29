#!/usr/bin/env python3
"""
tCam-Mini Proxy Server
Provides HTTP API access to tCam-Mini thermal data
Works around the limitation that tCam-Mini HTTP server only runs in AP mode
"""

from flask import Flask, jsonify, send_file
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
from datetime import datetime
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.tcam_ap_bridge import generate_mock_thermal_data

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for thermal data
thermal_cache = {
    'data': None,
    'timestamp': None,
    'stats': None
}

def update_thermal_cache():
    """Update the thermal data cache with mock data"""
    thermal_data = generate_mock_thermal_data()
    
    thermal_cache['data'] = thermal_data
    thermal_cache['timestamp'] = datetime.now()
    thermal_cache['stats'] = {
        'min_temp': float(np.min(thermal_data)),
        'max_temp': float(np.max(thermal_data)),
        'avg_temp': float(np.mean(thermal_data)),
        'median_temp': float(np.median(thermal_data)),
        'shape': thermal_data.shape
    }
    
    return thermal_data

@app.route('/')
def index():
    """Basic info endpoint"""
    return jsonify({
        'service': 'tCam-Mini Proxy Server',
        'status': 'running',
        'endpoints': {
            '/thermal_data': 'Get thermal image data as JSON',
            '/thermal_image': 'Get thermal image as PNG',
            '/thermal_stats': 'Get thermal statistics',
            '/status': 'Get device status'
        },
        'note': 'Using simulated data - tCam-Mini HTTP server only runs in AP mode'
    })

@app.route('/thermal_data')
def thermal_data():
    """Return thermal data as JSON"""
    try:
        # Update cache if needed (every 2 seconds)
        if (thermal_cache['timestamp'] is None or 
            (datetime.now() - thermal_cache['timestamp']).seconds > 2):
            update_thermal_cache()
        
        thermal_array = thermal_cache['data']
        
        return jsonify({
            'success': True,
            'thermal_data': thermal_array.tolist(),
            'shape': thermal_array.shape,
            'temperature_range': {
                'min': thermal_cache['stats']['min_temp'],
                'max': thermal_cache['stats']['max_temp'],
                'mean': thermal_cache['stats']['avg_temp'],
                'median': thermal_cache['stats']['median_temp']
            },
            'timestamp': thermal_cache['timestamp'].isoformat(),
            'data_source': 'simulated'
        })
        
    except Exception as e:
        logger.error(f"Error in thermal_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/thermal_image')
def thermal_image():
    """Return thermal image as PNG"""
    try:
        # Update cache if needed
        if (thermal_cache['timestamp'] is None or 
            (datetime.now() - thermal_cache['timestamp']).seconds > 2):
            update_thermal_cache()
        
        thermal_data = thermal_cache['data']
        
        # Create thermal image
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(thermal_data, cmap='hot', aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Temperature (°C)', rotation=270, labelpad=20)
        
        # Set labels and title
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_title(f'Thermal Image (Simulated) - {datetime.now().strftime("%H:%M:%S")}')
        
        # Save to BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close(fig)
        
        return send_file(img_buffer, mimetype='image/png')
        
    except Exception as e:
        logger.error(f"Error in thermal_image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/thermal_stats')
def thermal_stats():
    """Return thermal statistics"""
    try:
        # Update cache if needed
        if (thermal_cache['timestamp'] is None or 
            (datetime.now() - thermal_cache['timestamp']).seconds > 2):
            update_thermal_cache()
        
        return jsonify({
            'success': True,
            'stats': thermal_cache['stats'],
            'timestamp': thermal_cache['timestamp'].isoformat(),
            'data_source': 'simulated'
        })
        
    except Exception as e:
        logger.error(f"Error in thermal_stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/status')
def status():
    """Return device status"""
    return jsonify({
        'success': True,
        'device': {
            'name': 'tCam-Mini Proxy',
            'model': 'Simulated',
            'status': 'active',
            'connection': 'proxy_mode',
            'note': 'Real device at 192.168.1.130 but HTTP server only runs in AP mode'
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = 5002  # Different port from tCam-Mini
    logger.info(f"Starting tCam-Mini Proxy Server on port {port}")
    logger.info("This proxy provides simulated thermal data")
    logger.info("Real tCam-Mini HTTP server only runs in AP mode")
    
    # Initialize cache with first data
    update_thermal_cache()
    
    app.run(host='0.0.0.0', port=port, debug=False)
