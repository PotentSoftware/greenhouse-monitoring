#!/usr/bin/env python3
"""
Jetson Orin Nano Greenhouse Monitoring Server
Independent greenhouse monitoring system that operates concurrently with BeaglePlay
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config'))

import time
import threading
import logging
import json
import math
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib.colors import LinearSegmentedColormap
import io
import base64

# Import our modules
from sensor_manager import SensorManager
from vpd_calculator import VPDCalculator
from time_series_plotter import TimeSeriesPlotter
import jetson_config as config

# Thermal integration - handle import errors gracefully
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'thermal_segmentation'))
    from thermal_integration import create_thermal_integration
    THERMAL_FOLIAGE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Thermal foliage segmentation not available: {e}")
    THERMAL_FOLIAGE_AVAILABLE = False
    def create_thermal_integration():
        return None
from vpd_calculator import VPDCalculator
from thermal_processor import ThermalProcessor
from thermal_image_collector import ThermalImageCollector
from thermal_image_analyzer import ThermalImageAnalyzer
import jetson_config as config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)

class JetsonGreenhouseServer:
    def __init__(self):
        self.config = config
        self.sensor_manager = SensorManager(config)
        self.vpd_calculator = VPDCalculator()
        
        # Initialize time series plotter
        csv_path = os.path.join(config.DATA_DIR, config.CSV_FILE)
        self.plotter = TimeSeriesPlotter(csv_path, max_hours=2)
        self.thermal_processor = ThermalProcessor(config)
        self.thermal_collector = ThermalImageCollector(config, self.sensor_manager)
        self.thermal_analyzer = ThermalImageAnalyzer()
        self.thermal_foliage = create_thermal_integration() if THERMAL_FOLIAGE_AVAILABLE else None
        self.latest_analysis = None  # Store latest analysis results
        
        # Initialize data storage
        self.ensure_data_directory()
        
        # Combined sensor and calculated data
        self.current_data = {
            "timestamp": None,
            "sensors": {},
            "vpd": {},
            "thermal_processing": {},
            "system_info": {
                "jetson_ip": config.JETSON_IP,
                "jetson_port": config.JETSON_PORT,
                "version": "1.0.0",
                "concurrent_with_beagleplay": True
            }
        }
        
        # Start sensor update thread
        self.sensor_thread = threading.Thread(target=self.sensor_update_loop, daemon=True)
        self.sensor_thread.start()
        
        logging.info(f"🚀 Jetson Orin Nano Greenhouse Server initialized on {config.JETSON_IP}:{config.JETSON_PORT}")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs(config.DATA_DIR, exist_ok=True)
    
    def sensor_update_loop(self):
        """Main sensor update loop"""
        last_log_time = 0
        
        while True:
            try:
                # Update all sensors
                sensor_results = self.sensor_manager.update_all_sensors()
                sensor_data = self.sensor_manager.get_sensor_data()
                
                # Calculate VPD values
                vpd_data = self.vpd_calculator.calculate_all_vpd_types(sensor_data)
                
                # Process thermal image if available
                thermal_processing = {}
                thermal_image = sensor_data["thermal_camera"].get("raw_image")
                if thermal_image is not None:
                    thermal_processing = self.thermal_processor.process_thermal_image(thermal_image)
                    canopy_temp = self.thermal_processor.get_canopy_temperature(thermal_image)
                    thermal_processing["canopy_temperature"] = canopy_temp
                    
                    # Calculate foliage temperature using thermal segmentation
                    if self.thermal_foliage is not None:
                        try:
                            foliage_result = self.thermal_foliage.get_foliage_temperature()
                            thermal_processing["foliage_temperature"] = foliage_result.get("foliage_temperature", 0.0)
                            thermal_processing["foliage_segmentation"] = {
                                "segmentation_ratio": foliage_result.get("segmentation_ratio", 0.0),
                                "num_components": foliage_result.get("num_components", 0),
                                "processing_time": foliage_result.get("processing_time", 0.0),
                                "cuda_used": foliage_result.get("cuda_used", False),
                                "status": foliage_result.get("status", "unknown")
                            }
                        except Exception as e:
                            logging.warning(f"Foliage temperature calculation failed: {e}")
                            thermal_processing["foliage_temperature"] = 0.0
                            thermal_processing["foliage_segmentation"] = {
                                "segmentation_ratio": 0.0,
                                "num_components": 0,
                                "processing_time": 0.0,
                                "cuda_used": False,
                                "status": "error"
                            }
                    else:
                        thermal_processing["foliage_temperature"] = 0.0
                        thermal_processing["foliage_segmentation"] = {
                            "segmentation_ratio": 0.0,
                            "num_components": 0,
                            "processing_time": 0.0,
                            "cuda_used": False,
                            "status": "unavailable"
                        }
                
                # Add foliage temperature to sensor data for VPD calculation
                if "foliage_temperature" in thermal_processing:
                    sensor_data["foliage_temperature"] = {
                        "temperature": thermal_processing["foliage_temperature"]
                    }
                
                # Recalculate VPD with foliage temperature
                vpd_data = self.vpd_calculator.calculate_all_vpd_types(sensor_data)
                
                # Update combined data
                self.current_data = {
                    "timestamp": datetime.now().isoformat(),
                    "sensors": sensor_data,
                    "vpd": vpd_data,
                    "thermal_processing": thermal_processing,
                    "system_info": self.current_data["system_info"]
                }
                
                # Log data at specified interval
                current_time = time.time()
                if current_time - last_log_time >= config.LOG_INTERVAL:
                    self.log_data()
                    last_log_time = current_time
                
                time.sleep(config.SENSOR_READ_INTERVAL)
                
            except Exception as e:
                logging.error(f"❌ Sensor update loop error: {e}")
                time.sleep(5)
    
    def log_data(self):
        """Log sensor data to CSV and JSON files"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Get current sensor data
            data = self.current_data
            sensors = data["sensors"]
            vpd = data["vpd"]
            thermal_processing = data.get("thermal_processing", {})
            
            # Extract sensor values
            sht45_temp = sensors["feather_s3d"]["sht45"].get("temperature")
            sht45_humidity = sensors["feather_s3d"]["sht45"].get("humidity")
            hdc3022_temp = sensors["feather_s3d"]["hdc3022"].get("temperature")
            hdc3022_humidity = sensors["feather_s3d"]["hdc3022"].get("humidity")
            avg_temp = sensors["feather_s3d"]["averages"].get("temperature")
            avg_humidity = sensors["feather_s3d"]["averages"].get("humidity")
            
            # Thermal data
            thermal_min = sensors["thermal_camera"].get("min_temp")
            thermal_max = sensors["thermal_camera"].get("max_temp")
            thermal_avg = sensors["thermal_camera"].get("avg_temp")
            thermal_modal = sensors["thermal_camera"].get("modal_temp")
            
            # VPD data
            air_vpd = vpd.get("air_vpd")
            enhanced_vpd = vpd.get("enhanced_vpd")
            canopy_vpd_avg = vpd.get("canopy_vpd_avg")
            thermal_vpd = vpd.get("thermal_vpd")
            
            # Foliage data
            foliage_temperature = thermal_processing.get("foliage_temperature", 0.0)
            foliage_segmentation = thermal_processing.get("foliage_segmentation", {})
            segmentation_ratio = foliage_segmentation.get("segmentation_ratio", 0.0)
            enhanced_vpd_foliage = vpd.get("enhanced_vpd_foliage", 0.0)
            
            # Ensure data directory exists
            os.makedirs(config.DATA_DIR, exist_ok=True)
            
            # CSV logging
            csv_file = os.path.join(config.DATA_DIR, config.CSV_FILE)
            csv_row = [
                timestamp,
                sht45_temp, sht45_humidity,
                hdc3022_temp, hdc3022_humidity,
                avg_temp, avg_humidity,
                thermal_min, thermal_max, thermal_avg, thermal_modal,
                air_vpd, enhanced_vpd, canopy_vpd_avg, thermal_vpd,
                foliage_temperature, segmentation_ratio, enhanced_vpd_foliage
            ]
            
            # Write CSV header if file doesn't exist
            header = [
                "timestamp",
                "sht45_temp", "sht45_humidity",
                "hdc3022_temp", "hdc3022_humidity", 
                "avg_temp", "avg_humidity",
                "thermal_min", "thermal_max", "thermal_avg", "thermal_modal",
                "air_vpd", "enhanced_vpd", "canopy_vpd_avg", "thermal_vpd",
                "foliage_temperature", "segmentation_ratio", "enhanced_vpd_foliage"
            ]
            if not os.path.exists(csv_file):
                with open(csv_file, 'w') as f:
                    f.write(','.join(header) + '\n')
            
            # Append data
            with open(csv_file, 'a') as f:
                f.write(','.join(str(x) if x is not None else '' for x in csv_row) + '\n')
            
            # JSON logging (latest data)
            json_file = os.path.join(config.DATA_DIR, config.JSON_FILE)
            with open(json_file, 'w') as f:
                json.dump(self.current_data, f, indent=2, default=str)
            
            logging.info(f"📊 Jetson data logged: {len([x for x in csv_row[1:] if x is not None])} values")
            
        except Exception as e:
            logging.error(f"❌ Data logging error: {e}")

class JetsonHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Jetson greenhouse server"""
    
    def __init__(self, *args, server_instance=None, **kwargs):
        self.server_instance = server_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/':
                self.serve_dashboard()
            elif path == '/api/sensors':
                self.serve_sensor_data()
            elif path == '/api/thermal_image':
                self.serve_thermal_image()
            elif path == '/thermal_viewer':
                self.serve_thermal_viewer()
            elif path == '/thermal_image.png':
                self.serve_thermal_image_png()
            elif path == '/thermal_data.npy':
                self.serve_thermal_npy()
            elif path == '/api/thermal_pixel_data':
                self.serve_thermal_pixel_data()
            elif path == '/download/csv':
                self.serve_csv_download()
            elif path == '/plots':
                self.serve_plots_page()
            elif path == '/api/plots':
                self.serve_plots_api()
            elif path == '/api/sensors':
                self.serve_sensor_data()
            elif path == '/health':
                self.serve_health_check()
            elif path == '/analysis_results':
                self.serve_analysis_results()
            elif path == '/api/analysis_results':
                self.serve_analysis_results_api()
            elif path == '/api/get_available_collections':
                self.handle_get_available_collections()
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            logging.error(f"❌ HTTP handler error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/api/set_processing_strategy':
                self.handle_set_processing_strategy()
            elif path == '/api/collect_thermal_images':
                self.handle_collect_thermal_images()
            elif path == '/api/thermal_collection_status':
                self.handle_thermal_collection_status()
            elif path == '/api/get_available_collections':
                self.handle_get_available_collections()
            elif path == '/api/analyze_thermal_collection':
                self.handle_analyze_thermal_collection()
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            logging.error(f"❌ HTTP POST handler error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_dashboard(self):
        """Serve the main HTML dashboard"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Get current data
        data = self.server_instance.current_data
        sensors = data["sensors"]
        vpd = data["vpd"]
        
        # Generate time series plots
        plots = self.server_instance.plotter.generate_all_plots()
        
        # Extract sensor values with defaults
        sht45_temp = sensors["feather_s3d"]["sht45"].get("temperature", 0.0)
        sht45_humidity = sensors["feather_s3d"]["sht45"].get("humidity", 0.0)
        hdc3022_temp = sensors["feather_s3d"]["hdc3022"].get("temperature", 0.0)
        hdc3022_humidity = sensors["feather_s3d"]["hdc3022"].get("humidity", 0.0)
        avg_temp = sensors["feather_s3d"]["averages"].get("temperature", 0.0)
        avg_humidity = sensors["feather_s3d"]["averages"].get("humidity", 0.0)
        
        # Thermal data
        thermal_min = sensors["thermal_camera"].get("min_temp", 0.0)
        thermal_max = sensors["thermal_camera"].get("max_temp", 0.0)
        thermal_avg = sensors["thermal_camera"].get("avg_temp", 0.0)
        thermal_modal = sensors["thermal_camera"].get("modal_temp", 0.0)
        thermal_median = sensors["thermal_camera"].get("median_temp", 0.0)
        
        # Foliage temperature from thermal processing
        thermal_processing = data.get("thermal_processing", {})
        foliage_temp = thermal_processing.get("foliage_temperature", 0.0)
        foliage_segmentation = thermal_processing.get("foliage_segmentation", {})
        foliage_ratio = foliage_segmentation.get("segmentation_ratio", 0.0)
        foliage_components = foliage_segmentation.get("num_components", 0)
        foliage_processing_time = foliage_segmentation.get("processing_time", 0.0)
        foliage_cuda_used = foliage_segmentation.get("cuda_used", False)
        foliage_status = foliage_segmentation.get("status", "unknown")
        
        # VPD data
        air_vpd = vpd.get("air_vpd", 0.0)
        enhanced_vpd = vpd.get("enhanced_vpd", 0.0)
        canopy_vpd = vpd.get("canopy_vpd_avg", 0.0)
        
        # Enhanced VPD calculation using foliage temperature
        enhanced_vpd_foliage = vpd.get("enhanced_vpd_foliage", 0.0)
        if enhanced_vpd_foliage is None:
            enhanced_vpd_foliage = 0.0
        
        # Connection status
        feather_status = sensors["feather_s3d"]["connection_status"]
        thermal_status = sensors["thermal_camera"]["connection_status"]
        sensor_count = sensors["feather_s3d"]["sensor_count"]
        
        # Current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{config.DASHBOARD_TITLE}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @keyframes pulse {{
                    0% {{ opacity: 0.5; }}
                    50% {{ opacity: 1; }}
                    100% {{ opacity: 0.5; }}
                }}
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #121212; 
                    color: #e0e0e0; 
                }}
                
                .header {{ 
                    background-color: #1e1e1e; 
                    padding: 15px 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
                    text-align: center;
                    position: relative;
                }}
                
                .jetson-badge {{
                    position: absolute;
                    top: 15px;
                    left: 15px;
                    background-color: #76b900;
                    color: white;
                    padding: 8px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                
                .tools-container {{
                    position: absolute;
                    top: 15px;
                    right: 15px;
                }}
                
                .tools-button {{
                    background-color: #4caf50;
                    color: white;
                    padding: 10px 15px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.3s;
                }}
                
                .tools-button:hover {{
                    background-color: #45a049;
                }}
                
                .tools-dropdown {{
                    display: none;
                    position: absolute;
                    right: 0;
                    top: 100%;
                    background-color: #2d2d2d;
                    min-width: 200px;
                    box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2);
                    border-radius: 5px;
                    z-index: 1000;
                    margin-top: 2px;
                    border: 1px solid #4caf50;
                }}
                
                .tools-dropdown a {{
                    color: #ffffff;
                    padding: 12px 16px;
                    text-decoration: none;
                    display: block;
                    transition: background-color 0.3s;
                    border-bottom: 1px solid #444;
                }}
                
                .tools-dropdown a:last-child {{
                    border-bottom: none;
                }}
                
                .tools-dropdown a:hover {{
                    background-color: #4caf50;
                    color: #ffffff;
                }}
                
                .tools-dropdown.show {{
                    display: block !important;
                }}
                
                h1 {{ 
                    color: #76b900; 
                    margin: 0; 
                    padding: 0; 
                }}
                
                h2 {{ 
                    color: #ffffff; 
                    margin-top: 0; 
                }}
                
                .timestamp-header {{ 
                    color: #76b900; 
                    font-style: italic; 
                    margin: 10px 0 0 0; 
                    font-size: 16px; 
                    font-weight: normal; 
                }}
                
                .dashboard-container {{ 
                    display: flex; 
                    flex-wrap: wrap; 
                    justify-content: space-between; 
                    gap: 20px;
                }}
                
                .sensor-box {{ 
                    border: 1px solid #333; 
                    padding: 20px; 
                    border-radius: 8px; 
                    flex: 1; 
                    min-width: 200px; 
                    background-color: #1e1e1e; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
                    transition: transform 0.2s ease;
                }}
                
                .sensor-box:hover {{ 
                    transform: translateY(-5px); 
                }}
                
                .sensor-value {{ 
                    font-size: 28px; 
                    font-weight: bold; 
                    color: #76b900; 
                    margin-top: 10px; 
                    text-align: center; 
                }}
                
                .status-connected {{ color: #76b900; }}
                .status-disconnected {{ color: #f44336; }}
                
                .thermal-section {{ background-color: #2d1b00; }}
                .thermal-value {{ color: #ff9800; }}
                
                .vpd-section {{ background-color: #1a237e; }}
                .vpd-value {{ color: #2196f3; }}
                
                .greenhouse-section {{ background-color: #2d1b00; }}
                .greenhouse-value {{ color: #ff9800; }}
                .greenhouse-vpd {{ background-color: #1a237e; }}
                .greenhouse-vpd-value {{ color: #64b5f6; }}
                
                .tankroom-section {{ background-color: #0d4f3c; }}
                .tankroom-value {{ color: #4caf50; }}
                .tankroom-vpd {{ background-color: #0d47a1; }}
                .tankroom-vpd-value {{ color: #42a5f5; }}
                
                .foliage-section {{ background-color: #2e7d32; }}
                .foliage-value {{ color: #81c784; }}
                
                .enhanced-section {{ background-color: #0d4f3c; }}
                .enhanced-value {{ color: #4caf50; }}
                
                @media (max-width: 768px) {{ 
                    .dashboard-container {{ 
                        flex-direction: column; 
                    }}
                    .sensor-box {{ 
                        margin-bottom: 15px; 
                    }}
                }}
            </style>
            <script>
                function refreshData() {{
                    location.reload();
                }}
                
                function toggleTools() {{
                    var dropdown = document.getElementById("toolsDropdown");
                    dropdown.classList.toggle("show");
                }}
                
                // Close dropdown when clicking outside
                window.onclick = function(event) {{
                    if (!event.target.matches('.tools-button')) {{
                        var dropdowns = document.getElementsByClassName("tools-dropdown");
                        for (var i = 0; i < dropdowns.length; i++) {{
                            var openDropdown = dropdowns[i];
                            if (openDropdown.classList.contains('show')) {{
                                openDropdown.classList.remove('show');
                            }}
                        }}
                    }}
                }}
                
                // Auto-refresh every {config.AUTO_REFRESH_INTERVAL} seconds
                // Skip refresh if user is interacting with analysis controls
                setInterval(function() {{
                    const analysisInProgress = document.getElementById('analyzeBtn').innerHTML.includes('Processing') || 
                                             document.getElementById('analyzeBtn').innerHTML.includes('Analyzing') ||
                                             document.getElementById('analyzeBtn').innerHTML.includes('Starting');
                    const dropdownFocused = document.getElementById('analysisCollection') === document.activeElement;
                    const viewResultsActive = !document.getElementById('viewResultsBtn').disabled;
                    
                    if (!analysisInProgress && !dropdownFocused && !viewResultsActive) {{
                        refreshData();
                    }}
                }}, {config.AUTO_REFRESH_INTERVAL * 1000});
                
                // Thermal Image Collection Functions
                function startThermalCollection() {{
                    const numImages = parseInt(document.getElementById('numImages').value);
                    const intervalSeconds = parseInt(document.getElementById('intervalSeconds').value);
                    const button = document.getElementById('collectImagesBtn');
                    const status = document.getElementById('collectionStatus');
                    
                    // Disable button and show progress
                    button.disabled = true;
                    button.innerHTML = '⏳ Starting Collection...';
                    status.innerHTML = `Initializing collection of ${{numImages}} images every ${{intervalSeconds}} seconds...`;
                    status.style.color = '#ff9800';
                    
                    // Send collection request
                    fetch('/api/collect_thermal_images', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            num_images: numImages,
                            interval_seconds: intervalSeconds
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.status === 'started') {{
                            const estimatedTime = data.parameters.estimated_duration_seconds;
                            status.innerHTML = `✅ Collection started! Capturing ${{numImages}} images every ${{intervalSeconds}}s (Est. ${{estimatedTime}}s total)`;
                            status.style.color = '#4caf50';
                            
                            // Show countdown
                            let remainingTime = estimatedTime;
                            const countdown = setInterval(() => {{
                                remainingTime--;
                                if (remainingTime > 0) {{
                                    status.innerHTML = `📸 Collection in progress... (${{remainingTime}}s remaining)`;
                                }} else {{
                                    clearInterval(countdown);
                                    status.innerHTML = '🎉 Collection completed! Check ~/Desktop for thermal_collection_[timestamp] directory';
                                    status.style.color = '#4caf50';
                                    button.disabled = false;
                                    button.innerHTML = '📸 Collect Images';
                                }}
                            }}, 1000);
                            
                            // Re-enable button after estimated completion time + buffer
                            setTimeout(() => {{
                                button.disabled = false;
                                button.innerHTML = '📸 Collect Images';
                            }}, (estimatedTime + 5) * 1000);
                        }} else {{
                            status.innerHTML = '❌ Failed to start collection: ' + (data.message || 'Unknown error');
                            status.style.color = '#f44336';
                            button.disabled = false;
                            button.innerHTML = '📸 Collect Images';
                        }}
                    }})
                    .catch(error => {{
                        console.error('Collection error:', error);
                        status.innerHTML = '❌ Network error during collection request';
                        status.style.color = '#f44336';
                        button.disabled = false;
                        button.innerHTML = '📸 Collect Images';
                    }});
                }}
                
                // Analysis Functions
                function refreshCollections() {{
                    const dropdown = document.getElementById('analysisCollection');
                    const currentSelection = dropdown.value; // Preserve current selection
                    
                    fetch('/api/get_available_collections')
                    .then(response => response.json())
                    .then(data => {{
                        const button = document.getElementById('analyzeBtn');
                        const viewBtn = document.getElementById('viewResultsBtn');
                        const statusDiv = document.getElementById('analysisStatus');
                        
                        dropdown.innerHTML = '<option value="">Select collection...</option>';
                        
                        if (data.collections && data.collections.length > 0) {{
                            data.collections.forEach(collection => {{
                                const option = document.createElement('option');
                                option.value = collection.path;
                                option.textContent = `${{collection.name}} (${{collection.num_images}} images, ${{collection.size_mb.toFixed(1)}}MB)`;
                                dropdown.appendChild(option);
                            }});
                            
                            // Restore previous selection if it still exists
                            if (currentSelection) {{
                                dropdown.value = currentSelection;
                            }}
                            
                            dropdown.disabled = false;
                            
                            // Update button state based on current selection
                            if (dropdown.value) {{
                                button.disabled = false;
                                button.style.opacity = '1';
                                button.style.cursor = 'pointer';
                                if (viewBtn.style.display === 'none') {{
                                    statusDiv.innerHTML = 'Ready to analyze selected collection';
                                    statusDiv.style.color = '#76b900';
                                }}
                            }} else {{
                                button.disabled = true;
                                button.style.opacity = '0.6';
                                button.style.cursor = 'not-allowed';
                                if (viewBtn.style.display === 'none') {{
                                    statusDiv.innerHTML = 'Select a collection to analyze thermal images';
                                    statusDiv.style.color = '#888';
                                }}
                            }}
                            
                            // Enable analyze button when collection is selected
                            dropdown.onchange = function() {{
                                if (this.value) {{
                                    button.disabled = false;
                                    button.style.opacity = '1';
                                    button.style.cursor = 'pointer';
                                    if (viewBtn.style.display === 'none') {{
                                        statusDiv.innerHTML = 'Ready to analyze selected collection';
                                        statusDiv.style.color = '#76b900';
                                    }}
                                }} else {{
                                    button.disabled = true;
                                    button.style.opacity = '0.6';
                                    button.style.cursor = 'not-allowed';
                                    if (viewBtn.style.display === 'none') {{
                                        statusDiv.innerHTML = 'Select a collection to analyze thermal images';
                                        statusDiv.style.color = '#888';
                                    }}
                                }}
                            }}
                        }} else {{
                            dropdown.innerHTML = '<option value="">No collections found</option>';
                            dropdown.disabled = true;
                            button.disabled = true;
                            button.style.opacity = '0.6';
                            button.style.cursor = 'not-allowed';
                            if (viewBtn.style.display === 'none') {{
                                statusDiv.innerHTML = 'No thermal image collections available. Collect images first.';
                                statusDiv.style.color = '#888';
                            }}
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error fetching collections:', error);
                        if (document.getElementById('viewResultsBtn').style.display === 'none') {{
                            document.getElementById('analysisStatus').innerHTML = '&#x274C; Error loading collections';
                        }}
                    }});
                }}
                
                function resetAnalyzeButton() {{
                    const button = document.getElementById('analyzeBtn');
                    button.disabled = false;
                    button.style.opacity = '1';
                    button.style.cursor = 'pointer';
                    button.innerHTML = '&#x1F4CA; Analyze Images';
                }}
                
                function resetViewResultsButton() {{
                    const viewBtn = document.getElementById('viewResultsBtn');
                    viewBtn.disabled = true;
                    viewBtn.style.background = '#666';
                    viewBtn.style.color = '#999';
                    viewBtn.style.cursor = 'not-allowed';
                    viewBtn.style.opacity = '0.5';
                    viewBtn.style.pointerEvents = 'none';
                    viewBtn.style.animation = 'none';
                    viewBtn.innerHTML = '&#x1F4CB; View Results';
                }}
                
                function analyzeCollection() {{
                    const dropdown = document.getElementById('analysisCollection');
                    const button = document.getElementById('analyzeBtn');
                    const viewBtn = document.getElementById('viewResultsBtn');
                    const status = document.getElementById('analysisStatus');
                    
                    const collectionPath = dropdown.value;
                    if (!collectionPath) {{
                        status.innerHTML = '&#x274C; Please select a collection first';
                        status.style.color = '#f44336';
                        return;
                    }}
                    
                    // Disable view results button and add pulsing animation during analysis
                    viewBtn.disabled = true;
                    viewBtn.style.background = '#666';
                    viewBtn.style.color = '#999';
                    viewBtn.style.cursor = 'not-allowed';
                    viewBtn.style.opacity = '0.5';
                    viewBtn.style.pointerEvents = 'none';
                    viewBtn.style.animation = 'pulse 2s infinite';
                    
                    button.disabled = true;
                    button.style.opacity = '0.6';
                    button.style.cursor = 'not-allowed';
                    button.innerHTML = '&#x23F3; Starting...';
                    status.innerHTML = '&#x1F680; Initiating thermal image analysis...';
                    status.style.color = '#2196f3';
                    
                    // Start analysis
                    fetch('/api/analyze_thermal_collection', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            collection_path: collectionPath
                        }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        console.log('Analysis response:', data);
                        if (data.status === 'started') {{
                            status.innerHTML = '&#x1F504; Computing statistics and PCA... Please wait';
                            button.innerHTML = '&#x1F4CA; Analyzing...';
                            
                            // Poll for completion
                            let pollCount = 0;
                            const pollInterval = setInterval(() => {{
                                pollCount++;
                                const dots = '.'.repeat((pollCount % 4));
                                const minutes = Math.floor(pollCount * 2 / 60);
                                const seconds = (pollCount * 2) % 60;
                                status.innerHTML = '&#x1F9EE; Calculating Stats${{dots}} (${{minutes}}m ${{seconds}}s)';
                                
                                fetch('/api/analysis_results')
                                .then(response => response.json())
                                .then(results => {{
                                    console.log('Poll result:', results);
                                    
                                    // Check for successful completion
                                    if (results && results.collection_info && results.statistical_analysis && results.visualizations) {{
                                        clearInterval(pollInterval);
                                        status.innerHTML = '&#x2705; Analysis complete! Results are ready';
                                        status.style.color = '#4caf50';
                                        
                                        // Enable and style the view results button
                                        viewBtn.disabled = false;
                                        viewBtn.style.background = '#ff9800';
                                        
                                    }} else {{
                                        status.innerHTML = '&#x274C; Failed to start analysis: ' + (data.message || 'Unknown error');
                                        status.style.color = '#f44336';
                                        resetAnalyzeButton();
                                        resetViewResultsButton();
                                    }}
                                }})
                                .catch(error => {{
                                    console.error('Analysis error:', error);
                                    status.innerHTML = '&#x274C; Network error during analysis request';
                                    status.style.color = '#f44336';
                                    resetAnalyzeButton();
                                    resetViewResultsButton();
                                }});
                            }}, 2000); // Poll every 2 seconds
                            
                        }} else {{
                            status.innerHTML = '&#x274C; Failed to start analysis: ' + (data.message || 'Unknown error');
                            status.style.color = '#f44336';
                            resetAnalyzeButton();
                            resetViewResultsButton();
                        }}
                    }})
                    .catch(error => {{
                        console.error('Analysis error:', error);
                        status.innerHTML = '&#x274C; Network error during analysis request';
                        status.style.color = '#f44336';
                        resetAnalyzeButton();
                        resetViewResultsButton();
                    }});
                }}
                
                function viewResults() {{
                    window.open('/analysis_results', '_blank');
                }}
                
                // Load collections on page load
                document.addEventListener('DOMContentLoaded', function() {{
                    refreshCollections();
                }});
                
                function checkThermalCollectionStatus() {{
                    fetch('/api/thermal_collection_status', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        console.log('Thermal collection status:', data);
                    }})
                    .catch(error => {{
                        console.error('Status check error:', error);
                    }});
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <div class="jetson-badge">&#x1F916; JETSON ORIN NANO</div>
                <div class="tools-container">
                    <button class="tools-button" onclick="toggleTools()">Tools &#9662;</button>
                    <div class="tools-dropdown" id="toolsDropdown">
                        <a href="/plots">&#x1F4C8; Time Series Plots</a>
                        <a href="/thermal_viewer" target="_blank">&#x1F321; Thermal Image</a>
                        <a href="/download/csv">&#x1F4BE; Export Data</a>
                        <a href="/api/sensors">&#x1F4CA; JSON API</a>
                    </div>
                </div>
                <h1>{config.DASHBOARD_TITLE}</h1>
                <div class="timestamp-header">Last Updated: {current_time}</div>
                <div style="margin-top: 10px; font-size: 14px;">
                    Feather S3[D]: <span class="{'status-connected' if feather_status == 'connected' else 'status-disconnected'}">{feather_status}</span> | 
                    Sensors: {sensor_count}/2 | 
                    Thermal Camera: <span class="{'status-connected' if thermal_status == 'connected' else 'status-disconnected'}">{thermal_status}</span>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #888;">
                    Running independently on {config.JETSON_IP}:{config.JETSON_PORT} | Concurrent with BeaglePlay
                </div>
            </div>
            
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Greenhouse (SHT45 Sensor)</h2>
            <div class="dashboard-container">
                <div class="sensor-box greenhouse-section">
                    <h2>Temperature</h2>
                    <div class="sensor-value greenhouse-value">{sht45_temp:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box greenhouse-section">
                    <h2>Humidity</h2>
                    <div class="sensor-value greenhouse-value">{sht45_humidity:.1f} %RH</div>
                </div>
                
                <div class="sensor-box greenhouse-vpd">
                    <h2>Air VPD</h2>
                    <div class="sensor-value greenhouse-vpd-value">{vpd.get('sht45_vpd', 0.0):.2f} kPa</div>
                </div>
            </div>
            
            <h2 style="color: #4caf50; text-align: center; margin: 20px 0;">Tank Room (HDC3022 Sensor)</h2>
            <div class="dashboard-container">
                <div class="sensor-box tankroom-section">
                    <h2>Temperature</h2>
                    <div class="sensor-value tankroom-value">{hdc3022_temp:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box tankroom-section">
                    <h2>Humidity</h2>
                    <div class="sensor-value tankroom-value">{hdc3022_humidity:.1f} %RH</div>
                </div>
                
                <div class="sensor-box tankroom-vpd">
                    <h2>Air VPD</h2>
                    <div class="sensor-value tankroom-vpd-value">{vpd.get('hdc3022_vpd', 0.0):.2f} kPa</div>
                </div>
            </div>
            
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Thermal Camera Data</h2>
            <div class="dashboard-container">
                <div class="sensor-box thermal-section">
                    <h2>Min Temperature</h2>
                    <div class="sensor-value thermal-value">{thermal_min:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box thermal-section">
                    <h2>Max Temperature</h2>
                    <div class="sensor-value thermal-value">{thermal_max:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box thermal-section">
                    <h2>Mean Temperature</h2>
                    <div class="sensor-value thermal-value">{thermal_avg:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box thermal-section">
                    <h2>Median Temperature</h2>
                    <div class="sensor-value thermal-value">{thermal_median:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box thermal-section">
                    <h2>Modal Temperature</h2>
                    <div class="sensor-value thermal-value">{thermal_modal:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box foliage-section">
                    <h2>Foliage Temperature</h2>
                    <div class="sensor-value foliage-value">{foliage_temp:.1f} &deg;C</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Segmentation: {foliage_ratio:.1%} | Components: {foliage_components}<br>
                        CUDA: {'Yes' if foliage_cuda_used else 'No'} | Time: {foliage_processing_time:.3f}s
                    </div>
                </div>
            </div>
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Enhanced VPD (Foliage Temperature)</h2>
            <div class="dashboard-container">
                
                <div class="sensor-box enhanced-section">
                    <h2>VPD (Foliage Temperature & SHT45 %RH)</h2>
                    <div class="sensor-value enhanced-value">{enhanced_vpd_foliage:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Foliage Temp: {foliage_temp:.1f}&deg;C<br>
                        Humidity: SHT45 ({sht45_humidity:.1f}%RH)
                    </div>
                </div>
                
            </div>
            
            <!-- Thermal Image Collection Controls -->
            <div style="background: #2a2a2a; border: 2px solid #ff9800; border-radius: 10px; padding: 20px; margin: 20px auto; max-width: 800px;">
                <h3 style="color: #ff9800; text-align: center; margin: 0 0 15px 0;">&#x1F5BC; Thermal Image Collection for Analysis</h3>
                <div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <label style="color: #fff; font-weight: bold;">Images:</label>
                        <select id="numImages" style="padding: 5px; border-radius: 5px; border: 1px solid #ff9800; background: #1a1a1a; color: #fff;">
                            <option value="5">5 images</option>
                            <option value="10" selected>10 images</option>
                            <option value="15">15 images</option>
                            <option value="20">20 images</option>
                        </select>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <label style="color: #fff; font-weight: bold;">Interval:</label>
                        <select id="intervalSeconds" style="padding: 5px; border-radius: 5px; border: 1px solid #ff9800; background: #1a1a1a; color: #fff;">
                            <option value="3">3 seconds</option>
                            <option value="5" selected>5 seconds</option>
                            <option value="10">10 seconds</option>
                            <option value="15">15 seconds</option>
                        </select>
                    </div>
                    <button id="collectImagesBtn" onclick="startThermalCollection()" 
                            style="background: linear-gradient(135deg, #ff9800, #f57c00); color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.3s;">
                        &#x1F4F7; Collect Images
                    </button>
                </div>
                <div id="collectionStatus" style="margin-top: 15px; text-align: center; color: #888; font-size: 14px;">
                    Ready to collect thermal images for statistical analysis
                </div>
                <div style="margin-top: 10px; text-align: center; color: #666; font-size: 12px;">
                    Images saved as .npy files to ~/Desktop/thermal_collection_[timestamp]/
                </div>
                
                <!-- Analysis Section -->
                <div style="border-top: 1px solid #444; margin-top: 20px; padding-top: 20px;">
                    <h4 style="color: #76b900; text-align: center; margin: 0 0 15px 0;">&#x1F4C8; Statistical Analysis</h4>
                    <div style="display: flex; justify-content: center; align-items: center; gap: 15px; flex-wrap: wrap;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <label style="color: #fff; font-weight: bold;">Collection:</label>
                            <select id="analysisCollection" style="padding: 5px; border-radius: 5px; border: 1px solid #76b900; background: #1a1a1a; color: #fff; min-width: 200px;">
                                <option value="">Select collection...</option>
                            </select>
                            <button onclick="refreshCollections()" style="background: #444; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                                &#x1F504;
                            </button>
                            <button id="analyzeBtn" onclick="analyzeCollection()" style="background: #76b900; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; margin-left: 10px;" disabled>
                                &#x1F4CA; Analyze Images
                            </button>
                            <button id="viewResultsBtn" onclick="viewResults()" style="background: #666; color: #999; border: none; padding: 8px 16px; border-radius: 4px; cursor: not-allowed; font-size: 14px; margin-left: 10px; opacity: 0.5; pointer-events: none;" disabled>
                                &#x1F4CB; View Results
                            </button>
                        </div>
                    </div>
                    <div id="analysisStatus" style="margin-top: 15px; text-align: center; color: #888; font-size: 14px;">
                        Select a collection to analyze thermal images
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #1e1e1e; border-radius: 8px;">
                <h3 style="color: #76b900; margin-top: 0;">System Information</h3>
                <p style="margin: 5px 0;">&#x1F916; <strong>Jetson Orin Nano</strong> - Independent Greenhouse Monitoring</p>
                <p style="margin: 5px 0;">&#x1F4F1; Network: {config.JETSON_IP}:{config.JETSON_PORT}</p>
                <p style="margin: 5px 0;">&#x1F4F2; Concurrent Operation with BeaglePlay (192.168.1.203:8080)</p>
                <p style="margin: 5px 0;">&#x1F4CA; <a href="/api/sensors" style="color: #76b900;">JSON API</a> | 
                   &#x1F4BE; <a href="/download/csv" style="color: #76b900;">Download Data</a></p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def serve_thermal_image(self):
        """Serve thermal image data as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Access server instance directly from handler
        data = self.server_instance.current_data
        thermal_data = data["sensors"]["thermal_camera"]
        
        response = {
            "thermal_image": thermal_data.get("raw_image", "No thermal data available"),
            "min_temp": thermal_data.get("min_temp", 0.0),
            "max_temp": thermal_data.get("max_temp", 0.0),
            "avg_temp": thermal_data.get("avg_temp", 0.0),
            "modal_temp": thermal_data.get("modal_temp", 0.0),
            "median_temp": thermal_data.get("median_temp", 0.0),
            "stats": thermal_data.get("stats", {}),
            "timestamp": data["timestamp"]
        }
        
        json_data = json.dumps(response, indent=2, default=str)
        self.wfile.write(json_data.encode())
    
    def serve_thermal_viewer(self):
        """Serve thermal image viewer page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Get current thermal data for display
        data = self.server_instance.current_data
        thermal_data = data["sensors"]["thermal_camera"]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Jetson Orin Nano - Thermal Image Viewer</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #121212; 
                    color: #e0e0e0; 
                }}
                
                .header {{ 
                    background-color: #1e1e1e; 
                    padding: 15px 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
                    text-align: center;
                }}
                
                h1 {{ color: #76b900; }}
                h2 {{ color: #ffffff; }}
                
                .nav-button {{
                    background-color: #76b900;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 0 10px;
                    display: inline-block;
                    transition: background-color 0.3s;
                }}
                
                .nav-button:hover {{
                    background-color: #5a8a00;
                }}
                
                .content {{
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 25px;
                }}
                
                .thermal-panel {{
                    background: #2a2a2a;
                    padding: 25px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    border: 1px solid #404040;
                }}
                
                .info-panel {{
                    background: #2a2a2a;
                    padding: 25px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    border: 1px solid #404040;
                }}
                
                .thermal-image {{
                    max-width: 100%;
                    height: auto;
                    border: 2px solid #76b900;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(118, 185, 0, 0.3);
                    background-color: #2a2a2a;
                    transition: opacity 0.3s ease-in-out;
                    cursor: crosshair;
                }}
                
                .cursor-display {{
                    background: #1e1e1e;
                    border: 1px solid #404040;
                    border-radius: 5px;
                    padding: 8px 12px;
                    margin: 10px 0;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    color: #76b900;
                    text-align: center;
                }}
                
                .recorded-pixels-container {{
                    background: #1e1e1e;
                    border: 1px solid #404040;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 15px 0;
                }}
                
                .recorded-pixel {{
                    background: #2a2a2a;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 10px;
                    margin: 8px 0;
                    font-size: 13px;
                }}
                
                .temp-value {{
                    color: #76b900;
                    font-weight: bold;
                    font-size: 14px;
                }}
                
                .clear-button {{
                    background: #dc3545;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 13px;
                    margin-top: 10px;
                }}
                
                .clear-button:hover {{
                    background: #c82333;
                }}
                
                .stats {{
                    margin: 20px 0;
                }}
                
                .stat-item {{
                    margin: 10px 0;
                    padding: 12px;
                    background: #1e1e1e;
                    border-radius: 8px;
                    border-left: 4px solid #76b900;
                }}
                
                .stat-label {{
                    font-weight: bold;
                    color: #76b900;
                }}
                
                .stat-value {{
                    font-size: 1.2em;
                    color: #ffffff;
                }}
                
                .refresh-button {{
                    background-color: #ff9800;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin: 10px 0;
                }}
                
                .refresh-button:hover {{
                    background-color: #f57c00;
                }}
                
                @media (max-width: 768px) {{
                    .content {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
            <script>
                let thermalData = null;
                let recordedPixels = [];
                let imageWidth = 160;
                let imageHeight = 120;
                
                function refreshImage() {{
                    const img = document.getElementById('thermalImage');
                    const timestamp = new Date().getTime();
                    
                    // Create a new image element to preload the new image
                    const newImg = new Image();
                    newImg.onload = function() {{
                        // Only update the src when the new image is fully loaded
                        img.src = newImg.src;
                        // Fetch new thermal data for pixel interactions
                        fetchThermalData();
                    }};
                    newImg.onerror = function() {{
                        console.error('Failed to load thermal image');
                    }};
                    // Start loading the new image
                    newImg.src = '/thermal_image.png?' + timestamp;
                }}
                
                function fetchThermalData() {{
                    fetch('/api/thermal_pixel_data')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'success') {{
                                thermalData = data.thermal_data;
                                imageWidth = data.dimensions.width;
                                imageHeight = data.dimensions.height;
                                updateRecordedPixelTemperatures();
                            }}
                        }})
                        .catch(error => console.error('Error fetching thermal data:', error));
                }}
                
                function getPixelCoordinates(event) {{
                    const img = document.getElementById('thermalImage');
                    const rect = img.getBoundingClientRect();
                    const scaleX = imageWidth / rect.width;
                    const scaleY = imageHeight / rect.height;
                    
                    const x = Math.floor((event.clientX - rect.left) * scaleX);
                    const y = Math.floor((event.clientY - rect.top) * scaleY);
                    
                    return {{ x: Math.max(0, Math.min(x, imageWidth - 1)), y: Math.max(0, Math.min(y, imageHeight - 1)) }};
                }}
                
                function getPixelTemperature(x, y) {{
                    if (!thermalData || y >= thermalData.length || x >= thermalData[y].length) {{
                        return null;
                    }}
                    return thermalData[y][x];
                }}
                
                function updateCursorDisplay(event) {{
                    const coords = getPixelCoordinates(event);
                    const temp = getPixelTemperature(coords.x, coords.y);
                    const display = document.getElementById('cursorDisplay');
                    
                    if (temp !== null) {{
                        display.innerHTML = `Mouse: X=${{coords.x}}, Y=${{coords.y}}, Temp=${{temp.toFixed(1)}}&deg;C`;
                    }} else {{
                        display.innerHTML = 'Mouse: No data';
                    }}
                }}
                
                function recordPixel(event) {{
                    const coords = getPixelCoordinates(event);
                    const temp = getPixelTemperature(coords.x, coords.y);
                    
                    if (temp !== null) {{
                        const timestamp = new Date().toLocaleTimeString();
                        recordedPixels.push({{
                            x: coords.x,
                            y: coords.y,
                            temperature: temp,
                            timestamp: timestamp
                        }});
                        updateRecordedPixelsDisplay();
                    }}
                }}
                
                function updateRecordedPixelTemperatures() {{
                    // Update temperatures for existing recorded pixels with new thermal data
                    recordedPixels.forEach(pixel => {{
                        const newTemp = getPixelTemperature(pixel.x, pixel.y);
                        if (newTemp !== null) {{
                            pixel.currentTemperature = newTemp;
                        }}
                    }});
                    updateRecordedPixelsDisplay();
                }}
                
                function updateRecordedPixelsDisplay() {{
                    const container = document.getElementById('recordedPixels');
                    container.innerHTML = '';
                    
                    recordedPixels.forEach((pixel, index) => {{
                        const div = document.createElement('div');
                        div.className = 'recorded-pixel';
                        
                        let tempDisplay = `${{pixel.temperature.toFixed(1)}}&deg;C`;
                        if (pixel.currentTemperature !== undefined && pixel.currentTemperature !== pixel.temperature) {{
                            tempDisplay += ` -> ${{pixel.currentTemperature.toFixed(1)}}&deg;C`;
                        }}
                        
                        div.innerHTML = `
                            <strong>Pixel ${{index + 1}}:</strong> X=${{pixel.x}}, Y=${{pixel.y}}<br>
                            <span class="temp-value">${{tempDisplay}}</span><br>
                            <small>Recorded: ${{pixel.timestamp}}</small>
                        `;
                        container.appendChild(div);
                    }});
                }}
                
                function clearRecordedPixels() {{
                    recordedPixels = [];
                    updateRecordedPixelsDisplay();
                }}
                
                function autoRefresh() {{
                    refreshImage();
                    setTimeout(autoRefresh, 5000); // Refresh every 5 seconds
                }}
                
                window.onload = function() {{
                    const img = document.getElementById('thermalImage');
                    img.addEventListener('mousemove', updateCursorDisplay);
                    img.addEventListener('click', recordPixel);
                    
                    fetchThermalData();
                    autoRefresh();
                }};
            </script>
        </head>
        <body>
            <div class="header">
                <h1>&#x1F916; Jetson Orin Nano - Thermal Image Viewer</h1>
                <a href="/" class="nav-button">&#x2190; Back to Dashboard</a>
                <a href="/api/thermal_image" class="nav-button">&#x1F4CA; Raw Data</a>
                <a href="/thermal_data.npy" download class="nav-button">&#x1F4BE; Download .npy</a>
                <button onclick="refreshImage()" class="refresh-button">&#x1F504; Refresh Image</button>
            </div>
            
            <div class="content">
                <div class="thermal-panel">
                    <h2>&#x1F321; Live Thermal Image</h2>
                    <img id="thermalImage" src="/thermal_image.png" alt="Thermal Image" class="thermal-image">
                    <div id="cursorDisplay" class="cursor-display">
                        Move mouse over image to see pixel temperature
                    </div>
                    <p style="color: #888; text-align: center; margin-top: 10px;">
                        Auto-refreshing every 5 seconds • Click to record pixel values
                    </p>
                    
                    <div class="recorded-pixels-container">
                        <h3>&#x1F4CD; Recorded Pixels</h3>
                        <div id="recordedPixels">
                            <!-- Recorded pixels will be displayed here -->
                        </div>
                        <button onclick="clearRecordedPixels()" class="clear-button">Clear All</button>
                    </div>
                </div>
                
                <div class="info-panel">
                    <h2>&#x1F4CA; Temperature Statistics</h2>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-label">Minimum Temperature</div>
                            <div class="stat-value">{thermal_data.get("min_temp", 0.0):.1f}&deg;C</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Maximum Temperature</div>
                            <div class="stat-value">{thermal_data.get("max_temp", 0.0):.1f}&deg;C</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Average Temperature</div>
                            <div class="stat-value">{thermal_data.get("avg_temp", 0.0):.1f}&deg;C</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Modal Temperature</div>
                            <div class="stat-value">{thermal_data.get("modal_temp", 0.0):.1f}&deg;C</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Median Temperature</div>
                            <div class="stat-value">{thermal_data.get("median_temp", 0.0):.1f}&deg;C</div>
                        </div>
                    </div>
                    
                    <h2>&#x1F4CA; Image Statistics</h2>
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-label">Total Pixels</div>
                            <div class="stat-value">{thermal_data.get("stats", {}).get("total_pixels", 0):,}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Valid Pixels</div>
                            <div class="stat-value">{thermal_data.get("stats", {}).get("valid_pixels", 0):,}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Filtered Pixels</div>
                            <div class="stat-value">{thermal_data.get("stats", {}).get("negative_pixels_filtered", 0):,}</div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #1e1e1e; border-radius: 8px;">
                        <p style="margin: 0; color: #888; font-size: 14px;">
                            <strong>Last Updated:</strong><br>
                            {data["timestamp"]}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def serve_thermal_image_png(self):
        """Generate and serve thermal image as PNG"""
        try:
            # Get thermal data directly from sensor manager
            sensor_manager = self.server_instance.sensor_manager
            thermal_data = sensor_manager.sensor_data["thermal_camera"]
            
            # Get the actual numpy array from the sensor manager
            thermal_np = thermal_data.get("raw_image")
            
            if thermal_np is None or not isinstance(thermal_np, np.ndarray):
                # Fallback: create placeholder image
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.text(0.5, 0.5, 'No Real Thermal Data Available', 
                       horizontalalignment='center', verticalalignment='center',
                       transform=ax.transAxes, fontsize=16, color='white')
                ax.set_facecolor('black')
                fig.patch.set_facecolor('black')
            else:
                # Use the actual thermal camera data (160x120 numpy array)
                # Filter out negative values for display
                display_thermal = thermal_np.copy()
                display_thermal[display_thermal < 0] = np.nan  # Set negative values to NaN for proper display
                
                # Get temperature statistics
                min_temp = thermal_data.get("min_temp", 20.0)
                max_temp = thermal_data.get("max_temp", 30.0)
                avg_temp = thermal_data.get("avg_temp", 25.0)
            
                # Create thermal colormap
                colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                         '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
                thermal_cmap = LinearSegmentedColormap.from_list('thermal', colors, N=256)
                
                # Create the plot
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Display the real thermal image data
                im = ax.imshow(display_thermal, cmap=thermal_cmap, aspect='auto', 
                              vmin=min_temp, vmax=max_temp)
                
                # Add colorbar
                cbar = plt.colorbar(im, ax=ax, shrink=0.8)
                cbar.set_label('Temperature (C)', rotation=270, labelpad=20, color='white')
                cbar.ax.yaxis.set_tick_params(color='white')
                plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
                
                # Set title and labels with real data
                ax.set_title(f'Live Thermal Camera - Range: {min_temp:.1f}C to {max_temp:.1f}C (Avg: {avg_temp:.1f}C)', 
                            color='white', fontsize=14, pad=20)
                ax.set_xlabel('Pixel X (160 columns)', color='white')
                ax.set_ylabel('Pixel Y (120 rows)', color='white')
                
                # Style the plot
                ax.tick_params(colors='white')
                fig.patch.set_facecolor('black')
                ax.set_facecolor('black')
            
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', facecolor='black', 
                       bbox_inches='tight', dpi=100)
            img_buffer.seek(0)
            plt.close(fig)  # Important: close figure to free memory
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            self.wfile.write(img_buffer.getvalue())
            
        except Exception as e:
            logging.error(f"❌ Error generating thermal image: {e}")
            self.send_error(500, f"Error generating thermal image: {str(e)}")
    
    def serve_thermal_npy(self):
        """Serve thermal data as .npy file for download"""
        try:
            # Get thermal data directly from sensor manager
            sensor_manager = self.server_instance.sensor_manager
            thermal_data = sensor_manager.sensor_data["thermal_camera"]
            
            # Get the actual numpy array
            thermal_np = thermal_data.get("raw_image")
            
            if thermal_np is None or not isinstance(thermal_np, np.ndarray):
                self.send_error(404, "No thermal data available")
                return
            
            # Create .npy file in memory
            npy_buffer = io.BytesIO()
            np.save(npy_buffer, thermal_np)
            npy_buffer.seek(0)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thermal_data_{timestamp}.npy"
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(npy_buffer.getvalue())))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(npy_buffer.getvalue())
            
        except Exception as e:
            logging.error(f"❌ Error serving thermal .npy file: {e}")
            self.send_error(500, f"Error serving thermal data: {str(e)}")
    
    def serve_thermal_pixel_data(self):
        """Serve thermal pixel data as JSON for mouse interactions"""
        try:
            # Get thermal data directly from sensor manager
            sensor_manager = self.server_instance.sensor_manager
            thermal_data = sensor_manager.sensor_data["thermal_camera"]
            
            # Get the actual numpy array
            thermal_np = thermal_data.get("raw_image")
            
            if thermal_np is None or not isinstance(thermal_np, np.ndarray):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "status": "no_data",
                    "message": "No thermal data available"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Convert numpy array to nested list for JSON serialization
            thermal_list = thermal_np.tolist()
            
            response = {
                "status": "success",
                "thermal_data": thermal_list,
                "dimensions": {
                    "height": thermal_np.shape[0],
                    "width": thermal_np.shape[1]
                },
                "temperature_stats": {
                    "min_temp": thermal_data.get("min_temp", 0.0),
                    "max_temp": thermal_data.get("max_temp", 0.0),
                    "avg_temp": thermal_data.get("avg_temp", 0.0)
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            logging.error(f"❌ Error serving thermal pixel data: {e}")
            self.send_error(500, f"Error serving thermal pixel data: {str(e)}")
    
    def serve_csv_download(self):
        """Serve CSV data download"""
        try:
            # Access the server instance correctly - same pattern as serve_sensor_data
            server_instance = None
            if hasattr(self.server, 'server_instance'):
                server_instance = self.server.server_instance
            elif hasattr(self.server, 'greenhouse_server'):
                server_instance = self.server.greenhouse_server
            
            if not server_instance:
                self.send_error(500, "Server instance not available")
                return
                
            csv_file = os.path.join(server_instance.config.DATA_DIR, 'sensor_data.csv')
            
            if not os.path.exists(csv_file):
                self.send_error(404, "CSV file not found")
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="jetson_sensor_data.csv"')
            self.end_headers()
            
            with open(csv_file, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            logging.error(f"❌ CSV download error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_plots_page(self):
        """Serve time series plots page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Jetson Orin Nano - Time Series Plots</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #121212; 
                    color: #e0e0e0; 
                }}
                
                .header {{ 
                    background-color: #1e1e1e; 
                    padding: 15px 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
                    text-align: center;
                }}
                
                h1 {{ color: #76b900; }}
                h2 {{ color: #ffffff; }}
                
                .nav-button {{
                    background-color: #76b900;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 0 10px;
                    display: inline-block;
                    transition: background-color 0.3s;
                }}
                
                .nav-button:hover {{
                    background-color: #5a8a00;
                }}
                
                .controls {{
                    background-color: #1e1e1e;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }}
                
                .control-group {{
                    display: inline-block;
                    margin-right: 20px;
                }}
                
                label {{
                    color: #e0e0e0;
                    font-weight: bold;
                    margin-right: 10px;
                }}
                
                select {{
                    background-color: #2a2a2a;
                    color: #e0e0e0;
                    border: 1px solid #444;
                    padding: 5px 10px;
                    border-radius: 3px;
                }}
                
                button {{
                    background-color: #76b900;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 3px;
                    cursor: pointer;
                    margin-left: 10px;
                }}
                
                button:hover {{
                    background-color: #5a8a00;
                }}
                
                .plot-container {{
                    background-color: #1e1e1e;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>&#x1F916; Jetson Orin Nano - Time Series Plots</h1>
                <a href="/" class="nav-button">&#x2190; Back to Dashboard</a>
                <a href="/download/csv" class="nav-button">&#x1F4BE; Download Data</a>
            </div>
            
            <div class="controls">
                <h3>📊 Plot Controls</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 15px;">
                    <div class="control-group">
                        <label for="tempYMode">🌡️ Temperature Y-Axis:</label>
                        <select id="tempYMode">
                            <option value="data_range" selected>Data Range + Margin</option>
                            <option value="auto">Auto Scale</option>
                            <option value="tight">Tight Fit</option>
                            <option value="fixed">Fixed Range</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="humidityYMode">💧 Humidity Y-Axis:</label>
                        <select id="humidityYMode">
                            <option value="data_range" selected>Data Range + Margin</option>
                            <option value="auto">Auto Scale</option>
                            <option value="tight">Tight Fit</option>
                            <option value="fixed">Fixed Range</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="vpdYMode">📊 VPD Y-Axis:</label>
                        <select id="vpdYMode">
                            <option value="data_range" selected>Data Range + Margin</option>
                            <option value="auto">Auto Scale</option>
                            <option value="tight">Tight Fit</option>
                            <option value="fixed">Fixed Range</option>
                        </select>
                    </div>
                    <div class="control-group">
                        <label for="foliageYMode">🌿 Foliage Y-Axis:</label>
                        <select id="foliageYMode">
                            <option value="data_range" selected>Data Range + Margin</option>
                            <option value="auto">Auto Scale</option>
                            <option value="tight">Tight Fit</option>
                            <option value="fixed">Fixed Range</option>
                        </select>
                    </div>
                </div>
                <div class="control-group" style="text-align: center;">
                    <button onclick="updatePlots()" style="margin-right: 10px;">Update All Plots</button>
                    <button onclick="loadPlots()" style="margin-right: 10px;">🔄 Refresh</button>
                    <span id="lastUpdate" style="color: #888; font-size: 12px;">Never updated</span>
                </div>
            </div>
            
            <div class="plot-container">
                <h2>&#x1F4C8; Time Series Analysis</h2>
                <div id="plotsContainer">
                    <p>Loading time series plots...</p>
                </div>
            </div>
            
            <script>
                let isLoading = false;
                
                function loadPlots(tempYMode = 'data_range', humidityYMode = 'data_range', vpdYMode = 'data_range', foliageYMode = 'data_range') {{
                    if (isLoading) {{
                        return;
                    }}
                    
                    isLoading = true;
                    
                    // Build query string with individual y-axis modes
                    const params = new URLSearchParams({{
                        'temperature_y_mode': tempYMode,
                        'humidity_y_mode': humidityYMode,
                        'vpd_y_mode': vpdYMode,
                        'foliage_y_mode': foliageYMode,
                        '_t': new Date().getTime()
                    }});
                    
                    const url = '/api/plots?' + params.toString();
                    console.log('Loading plots with individual y-axis modes:', {{tempYMode, humidityYMode, vpdYMode, foliageYMode}});
                    
                    fetch(url)
                        .then(response => response.json())
                        .then(plots => {{
                            const container = document.getElementById('plotsContainer');
                            let html = '';
                            
                            if (plots.temperature) {{
                                html += '<div class="plot-wrapper" style="margin: 20px 0; overflow-x: auto; position: relative;"><h3>🌡️ Temperature Trends (Y-axis: ' + tempYMode + ')</h3><img src="' + plots.temperature + '" style="max-width: none; width: 1200px; height: auto; border-radius: 10px; cursor: crosshair;" alt="Temperature Plot" onmousemove="showTemperatureTooltip(event, this)" onmouseout="hideTooltipDelayed()"><div id="temperature-tooltip" class="plot-tooltip" style="position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 3px; display: none; pointer-events: none; z-index: 1000;"></div></div>';
                            }}
                            
                            if (plots.humidity) {{
                                html += '<div class="plot-wrapper" style="margin: 20px 0; overflow-x: auto; position: relative;"><h3>💧 Humidity Trends (Y-axis: ' + humidityYMode + ')</h3><img src="' + plots.humidity + '" style="max-width: none; width: 1200px; height: auto; border-radius: 10px; cursor: crosshair;" alt="Humidity Plot" onmousemove="showHumidityTooltip(event, this)" onmouseout="hideTooltipDelayed()"><div id="humidity-tooltip" class="plot-tooltip" style="position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 3px; display: none; pointer-events: none; z-index: 1000;"></div></div>';
                            }}
                            
                            if (plots.vpd) {{
                                html += '<div class="plot-wrapper" style="margin: 20px 0; overflow-x: auto; position: relative;"><h3>📊 VPD Analysis (Y-axis: ' + vpdYMode + ')</h3><img src="' + plots.vpd + '" style="max-width: none; width: 1200px; height: auto; border-radius: 10px; cursor: crosshair;" alt="VPD Plot" onmousemove="showVpdTooltip(event, this)" onmouseout="hideTooltipDelayed()"><div id="vpd-tooltip" class="plot-tooltip" style="position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 3px; display: none; pointer-events: none; z-index: 1000;"></div></div>';
                            }}
                            
                            if (plots.foliage) {{
                                html += '<div class="plot-wrapper" style="margin: 20px 0; overflow-x: auto; position: relative;"><h3>🌿 Foliage Temperature Analysis (Y-axis: ' + foliageYMode + ')</h3><img src="' + plots.foliage + '" style="max-width: none; width: 1200px; height: auto; border-radius: 10px; cursor: crosshair;" alt="Foliage Plot" onmousemove="showFoliageTooltip(event, this)" onmouseout="hideTooltipDelayed()"><div id="foliage-tooltip" class="plot-tooltip" style="position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 3px; display: none; pointer-events: none; z-index: 1000;"></div></div>';
                            }}
                            
                            if (html === '') {{
                                html = '<p style="color: #888;">No plot data available. Please wait for data collection...</p>';
                            }}
                            
                            container.innerHTML = html;
                            
                            // Auto-scroll all plot containers to the right to show latest data
                            setTimeout(() => {{
                                const plotWrappers = document.querySelectorAll('.plot-wrapper');
                                plotWrappers.forEach(wrapper => {{
                                    wrapper.scrollLeft = wrapper.scrollWidth - wrapper.clientWidth;
                                }});
                            }}, 100);
                            
                            // Update last refresh time
                            const now = new Date();
                            document.getElementById('lastUpdate').textContent = 'Last updated: ' + now.toLocaleTimeString();
                            
                            isLoading = false;
                        }})
                        .catch(error => {{
                            console.error('Error loading plots:', error);
                            document.getElementById('plotsContainer').innerHTML = '<p style="color: #f44336;">Error loading plots: ' + error.message + '</p>';
                            isLoading = false;
                        }});
                }}
                
                function updatePlots() {{
                    // Get individual y-axis modes for each plot type
                    const tempYMode = document.getElementById('tempYMode').value;
                    const humidityYMode = document.getElementById('humidityYMode').value;
                    const vpdYMode = document.getElementById('vpdYMode').value;
                    const foliageYMode = document.getElementById('foliageYMode').value;
                    
                    console.log('Update button clicked, modes:', {{tempYMode, humidityYMode, vpdYMode, foliageYMode}});
                    loadPlots(tempYMode, humidityYMode, vpdYMode, foliageYMode);
                }}
                
                function getCurrentYModes() {{
                    return {{
                        tempYMode: document.getElementById('tempYMode').value,
                        humidityYMode: document.getElementById('humidityYMode').value,
                        vpdYMode: document.getElementById('vpdYMode').value,
                        foliageYMode: document.getElementById('foliageYMode').value
                    }};
                }}
                
                // Load plots on page load
                document.addEventListener('DOMContentLoaded', function() {{
                    loadPlots();
                }});
                
                // Refresh plots every 5 seconds with current y-axis modes
                setInterval(() => {{
                    if (!isLoading) {{
                        const modes = getCurrentYModes();
                        loadPlots(modes.tempYMode, modes.humidityYMode, modes.vpdYMode, modes.foliageYMode);
                    }}
                }}, 5000);
                
                // Global tooltip timeout variable
                let tooltipTimeout;
                
                // Tooltip functions for interactive hover
                function showTemperatureTooltip(event, img) {{
                    clearTimeout(tooltipTimeout);
                    const tooltip = document.getElementById('temperature-tooltip');
                    const rect = img.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;
                    
                    // Calculate approximate data values based on mouse position
                    const xPercent = x / rect.width;
                    const yPercent = (rect.height - y) / rect.height;
                    
                    // Mock data calculation (would need actual data mapping for precision)
                    const timeOffset = xPercent * 2; // 2 hours of data
                    const now = new Date();
                    const dataTime = new Date(now.getTime() - (2 - timeOffset) * 60 * 60 * 1000);
                    const tempValue = (20 + yPercent * 15).toFixed(1); // Mock temperature range 20-35°C
                    
                    tooltip.innerHTML = `Time: ${{dataTime.toLocaleTimeString()}}<br>Temperature: ${{tempValue}}°C`;
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 10) + 'px';
                    tooltip.style.display = 'block';
                }}
                
                function showHumidityTooltip(event, img) {{
                    clearTimeout(tooltipTimeout);
                    const tooltip = document.getElementById('humidity-tooltip');
                    const rect = img.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;
                    
                    const xPercent = x / rect.width;
                    const yPercent = (rect.height - y) / rect.height;
                    
                    const timeOffset = xPercent * 2;
                    const now = new Date();
                    const dataTime = new Date(now.getTime() - (2 - timeOffset) * 60 * 60 * 1000);
                    const humidityValue = (30 + yPercent * 40).toFixed(1); // Mock humidity range 30-70%
                    
                    tooltip.innerHTML = `Time: ${{dataTime.toLocaleTimeString()}}<br>Humidity: ${{humidityValue}}%RH`;
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 10) + 'px';
                    tooltip.style.display = 'block';
                }}
                
                function showVpdTooltip(event, img) {{
                    clearTimeout(tooltipTimeout);
                    const tooltip = document.getElementById('vpd-tooltip');
                    const rect = img.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;
                    
                    const xPercent = x / rect.width;
                    const yPercent = (rect.height - y) / rect.height;
                    
                    const timeOffset = xPercent * 2;
                    const now = new Date();
                    const dataTime = new Date(now.getTime() - (2 - timeOffset) * 60 * 60 * 1000);
                    const vpdValue = (0.5 + yPercent * 1.5).toFixed(2); // Mock VPD range 0.5-2.0 kPa
                    
                    tooltip.innerHTML = `Time: ${{dataTime.toLocaleTimeString()}}<br>VPD: ${{vpdValue}} kPa`;
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 10) + 'px';
                    tooltip.style.display = 'block';
                }}
                
                function showFoliageTooltip(event, img) {{
                    clearTimeout(tooltipTimeout);
                    const tooltip = document.getElementById('foliage-tooltip');
                    const rect = img.getBoundingClientRect();
                    const x = event.clientX - rect.left;
                    const y = event.clientY - rect.top;
                    
                    const xPercent = x / rect.width;
                    const yPercent = (rect.height - y) / rect.height;
                    
                    const timeOffset = xPercent * 2;
                    const now = new Date();
                    const dataTime = new Date(now.getTime() - (2 - timeOffset) * 60 * 60 * 1000);
                    const foliageValue = (22 + yPercent * 8).toFixed(1); // Mock foliage temp range 22-30°C
                    
                    tooltip.innerHTML = `Time: ${{dataTime.toLocaleTimeString()}}<br>Foliage Temp: ${{foliageValue}}°C`;
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 10) + 'px';
                    tooltip.style.display = 'block';
                }}
                
                function hideTooltipDelayed() {{
                    // Hide tooltip after 3 seconds to allow reading during updates
                    tooltipTimeout = setTimeout(() => {{
                        const tooltips = document.querySelectorAll('.plot-tooltip');
                        tooltips.forEach(tooltip => {{
                            tooltip.style.display = 'none';
                        }});
                    }}, 3000);
                }}
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def serve_plots_api(self):
        """Serve time series plots as JSON API"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Parse query parameters for y-axis scaling
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # Valid y-axis modes
            valid_modes = ['auto', 'tight', 'fixed', 'data_range']
            
            # Parse individual y-axis modes for each plot type
            y_modes = {}
            for plot_type in ['temperature', 'humidity', 'vpd', 'foliage']:
                y_mode = query_params.get(f'{plot_type}_y_mode', ['data_range'])[0]
                if y_mode not in valid_modes:
                    y_mode = 'data_range'
                y_modes[plot_type] = y_mode
            
            # Also support legacy single y_mode parameter
            if 'y_mode' in query_params:
                legacy_mode = query_params.get('y_mode', ['data_range'])[0]
                if legacy_mode in valid_modes:
                    for plot_type in y_modes:
                        y_modes[plot_type] = legacy_mode
            
            plots = self.server_instance.plotter.generate_all_plots(y_modes)
            json_data = json.dumps(plots, indent=2)
            self.wfile.write(json_data.encode())
        except Exception as e:
            logging.error(f"❌ Plots API error: {e}")
            error_response = json.dumps({"error": str(e)})
            self.wfile.write(error_response.encode())
    
    def serve_sensor_data(self):
        """Serve sensor data as JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(self.server_instance.current_data, indent=2, default=str)
        self.wfile.write(json_data.encode())
    
    def serve_health_check(self):
        """Serve health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "jetson_ip": config.JETSON_IP,
            "jetson_port": config.JETSON_PORT,
            "sensors_connected": {
                "feather_s3d": self.server_instance.current_data["sensors"]["feather_s3d"]["connection_status"] == "connected",
                "thermal_camera": self.server_instance.current_data["sensors"]["thermal_camera"]["connection_status"] == "connected"
            }
        }
        
        json_data = json.dumps(health_data, indent=2)
        self.wfile.write(json_data.encode())
    
    def serve_csv_download(self):
        """Serve CSV data download"""
        try:
            csv_file = os.path.join(config.DATA_DIR, config.CSV_FILE)
            if os.path.exists(csv_file):
                self.send_response(200)
                self.send_header('Content-type', 'text/csv')
                self.send_header('Content-Disposition', f'attachment; filename="{config.CSV_FILE}"')
                self.end_headers()
                
                with open(csv_file, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "CSV file not found")
        except Exception as e:
            logging.error(f"❌ CSV download error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_collect_thermal_images(self):
        """Handle thermal image collection request"""
        try:
            # Parse request parameters
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode('utf-8'))
            else:
                params = {}
            
            # Get parameters with defaults
            num_images = params.get('num_images', 10)
            interval_seconds = params.get('interval_seconds', 5)
            
            # Validate parameters
            if not isinstance(num_images, int) or num_images < 1 or num_images > 50:
                self.send_error(400, "Invalid num_images parameter (1-50)")
                return
            
            if not isinstance(interval_seconds, int) or interval_seconds < 1 or interval_seconds > 60:
                self.send_error(400, "Invalid interval_seconds parameter (1-60)")
                return
            
            logging.info(f"🎯 Starting thermal image collection: {num_images} images, {interval_seconds}s intervals")
            
            # Start collection in background thread to avoid blocking HTTP response
            def collect_images():
                try:
                    result = self.server_instance.thermal_collector.collect_image_series(
                        num_images=num_images,
                        interval_seconds=interval_seconds
                    )
                    logging.info(f"✅ Thermal collection completed: {result['images_captured']}/{result['total_requested']} images")
                except Exception as e:
                    logging.error(f"❌ Thermal collection error: {e}")
            
            collection_thread = threading.Thread(target=collect_images, daemon=True)
            collection_thread.start()
            
            # Send immediate response
            response_data = {
                "status": "started",
                "message": f"Thermal image collection started: {num_images} images, {interval_seconds}s intervals",
                "parameters": {
                    "num_images": num_images,
                    "interval_seconds": interval_seconds,
                    "estimated_duration_seconds": num_images * interval_seconds
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request body")
        except Exception as e:
            logging.error(f"❌ Thermal collection handler error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_thermal_collection_status(self):
        """Handle thermal collection status request"""
        try:
            status = self.server_instance.thermal_collector.get_collection_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            
        except Exception as e:
            logging.error(f"❌ Thermal collection status error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_get_available_collections(self):
        """Handle request for available thermal image collections"""
        try:
            collections = self.server_instance.thermal_analyzer.get_available_collections()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"collections": collections}).encode())
            
        except Exception as e:
            logging.error(f"❌ Get collections error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def handle_analyze_thermal_collection(self):
        """Handle thermal image collection analysis request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            
            collection_path = params.get('collection_path')
            if not collection_path:
                self.send_error(400, "Missing collection_path parameter")
                return
            
            # Perform analysis in background thread to avoid blocking
            def analyze_collection():
                try:
                    analysis_results = self.server_instance.thermal_analyzer.analyze_image_collection(collection_path)
                    # Store results for retrieval
                    self.server_instance.latest_analysis = analysis_results
                    logging.info(f"✅ Analysis complete for collection: {collection_path}")
                except Exception as e:
                    logging.error(f"❌ Analysis failed: {e}")
                    self.server_instance.latest_analysis = {"error": str(e)}
            
            analysis_thread = threading.Thread(target=analyze_collection, daemon=True)
            analysis_thread.start()
            
            # Send immediate response
            response_data = {
                "status": "started",
                "message": "Analysis started in background",
                "collection_path": collection_path
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            logging.error(f"❌ Analysis handler error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_analysis_results_api(self):
        """Serve analysis results as JSON API"""
        try:
            if hasattr(self.server_instance, 'latest_analysis') and self.server_instance.latest_analysis:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(self.server_instance.latest_analysis).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No analysis results available"}).encode())
        except Exception as e:
            logging.error(f"❌ Analysis results API error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_analysis_results(self):
        """Serve analysis results HTML page"""
        try:
            if not hasattr(self.server_instance, 'latest_analysis') or not self.server_instance.latest_analysis:
                self.send_error(404, "No analysis results available")
                return
            
            results = self.server_instance.latest_analysis
            
            if 'error' in results:
                self.send_error(500, f"Analysis error: {results['error']}")
                return
            
            # Generate HTML page with results
            html = self._generate_analysis_results_html(results)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())
            
        except Exception as e:
            logging.error(f"❌ Analysis results page error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def _generate_analysis_results_html(self, results):
        """Generate comprehensive HTML page for analysis results"""
        collection_info = results['collection_info']
        stats = results['statistical_analysis']
        pca = results['pca_analysis']
        viz = results['visualizations']
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Thermal Image Analysis Results</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
                    color: #ffffff;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding: 30px;
                    background: linear-gradient(135deg, #ff9800, #f57c00);
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(255, 152, 0, 0.3);
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: bold;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .info-card {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 25px;
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    backdrop-filter: blur(10px);
                }}
                .info-card h3 {{
                    color: #ff9800;
                    margin-top: 0;
                    font-size: 1.3em;
                }}
                .stat-value {{
                    font-size: 1.8em;
                    font-weight: bold;
                    color: #76b900;
                    margin: 10px 0;
                }}
                .visualization {{
                    text-align: center;
                    margin: 40px 0;
                    padding: 30px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .visualization h3 {{
                    color: #76b900;
                    margin-bottom: 20px;
                    font-size: 1.5em;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }}
                .stats-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    overflow: hidden;
                }}
                .stats-table th, .stats-table td {{
                    padding: 15px;
                    text-align: left;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }}
                .stats-table th {{
                    background: rgba(255, 152, 0, 0.2);
                    color: #ff9800;
                    font-weight: bold;
                }}
                .back-button {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #76b900, #5a8a00);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: bold;
                    text-decoration: none;
                    box-shadow: 0 4px 15px rgba(118, 185, 0, 0.3);
                    transition: all 0.3s;
                }}
                .back-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(118, 185, 0, 0.4);
                }}
                .pca-summary {{
                    background: linear-gradient(135deg, #76b900, #5a8a00);
                    padding: 20px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <a href="javascript:window.close()" class="back-button">✕ Close</a>
            
            <div class="container">
                <div class="header">
                    <h1>&#x1F4CA; Thermal Image Analysis Results</h1>
                    <p>Statistical Analysis & Principal Component Analysis</p>
                </div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <h3>&#x1F4C1; Collection Information</h3>
                        <p><strong>Path:</strong> {collection_info['path']}</p>
                        <p><strong>Images:</strong> {collection_info['num_images']}</p>
                        <p><strong>Resolution:</strong> {collection_info['image_shape'][0]}×{collection_info['image_shape'][1]}</p>
                        <p><strong>Analyzed:</strong> {collection_info['analysis_timestamp'][:19].replace('T', ' ')}</p>
                    </div>
                    
                    <div class="info-card">
                        <h3>&#x1F321;&#xFE0F; Temperature Statistics</h3>
                        <p>Mean: <span class="stat-value">{stats['global_statistics']['mean']:.2f}°C</span></p>
                        <p>Median: <span class="stat-value">{stats['global_statistics']['median']:.2f}°C</span></p>
                        <p>Mode: <span class="stat-value">{stats['global_statistics']['mode']:.2f}°C</span></p>
                        <p>Std Dev: <span class="stat-value">{stats['global_statistics']['std']:.2f}°C</span></p>
                    </div>
                    
                    <div class="info-card">
                        <h3>&#x1F4C8; PCA Summary</h3>
                        <p>Total Components: <span class="stat-value">{pca['n_components']}</span></p>
                        <p>95% Variance: <span class="stat-value">{pca['n_components_95_variance']}</span> components</p>
                        <p>PC1 Variance: <span class="stat-value">{pca['explained_variance_ratio'][0]*100:.1f}%</span></p>
                        <p>PC2 Variance: <span class="stat-value">{pca['explained_variance_ratio'][1]*100:.1f}%</span></p>
                    </div>
                    
                    <div class="info-card">
                        <h3>&#x1F4CF; Data Distribution</h3>
                        <p>Range: <span class="stat-value">{stats['global_statistics']['min']:.1f}°C - {stats['global_statistics']['max']:.1f}°C</span></p>
                        <p>Q25-Q75: <span class="stat-value">{stats['global_statistics']['q25']:.1f}°C - {stats['global_statistics']['q75']:.1f}°C</span></p>
                        <p>Skewness: <span class="stat-value">{stats['global_statistics']['skewness']:.3f}</span></p>
                        <p>Kurtosis: <span class="stat-value">{stats['global_statistics']['kurtosis']:.3f}</span></p>
                    </div>
                </div>
        """
        
        # Add visualizations
        for viz_name, viz_data in viz.items():
            viz_title = viz_name.replace('_', ' ').title()
            html += f"""
                <div class="visualization">
                    <h3>{viz_title}</h3>
                    <img src="data:image/png;base64,{viz_data}" alt="{viz_title}">
                </div>
            """
        
        # Add per-image statistics table
        html += f"""
                <div class="visualization">
                    <h3>Per-Image Statistics</h3>
                    <table class="stats-table">
                        <thead>
                            <tr>
                                <th>Image</th>
                                <th>Mean (°C)</th>
                                <th>Median (°C)</th>
                                <th>Mode (°C)</th>
                                <th>Std Dev (°C)</th>
                                <th>Min (°C)</th>
                                <th>Max (°C)</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for i, img_stats in enumerate(stats['per_image_statistics']):
            html += f"""
                            <tr>
                                <td>Image {i+1}</td>
                                <td>{img_stats['mean']:.2f}</td>
                                <td>{img_stats['median']:.2f}</td>
                                <td>{img_stats['mode']:.2f}</td>
                                <td>{img_stats['std']:.2f}</td>
                                <td>{img_stats['min']:.2f}</td>
                                <td>{img_stats['max']:.2f}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def handle_set_processing_strategy(self):
        """Handle thermal processing strategy change request"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode('utf-8'))
            else:
                params = {}
            
            strategy = params.get('strategy', 'basic')
            success = self.server_instance.thermal_processor.set_processing_strategy(strategy)
            
            response_data = {
                "status": "success" if success else "error",
                "strategy": strategy,
                "message": f"Processing strategy {'set to' if success else 'failed to set to'} {strategy}"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON in request body")
        except Exception as e:
            logging.error(f"❌ Processing strategy handler error: {e}")
            self.send_error(500, "Internal Server Error")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server"""
    pass

def create_handler_class(server_instance):
    """Create handler class with server instance"""
    class Handler(JetsonHTTPHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, server_instance=server_instance, **kwargs)
    return Handler

def main():
    """Main function"""
    try:
        # Create server instance
        server_instance = JetsonGreenhouseServer()
        
        # Create HTTP server
        handler_class = create_handler_class(server_instance)
        httpd = ThreadedHTTPServer((config.JETSON_IP, config.JETSON_PORT), handler_class)
        
        logging.info(f"🌐 Jetson Greenhouse Server starting on http://{config.JETSON_IP}:{config.JETSON_PORT}")
        logging.info(f"🔄 Operating independently and concurrently with BeaglePlay")
        
        # Start server
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logging.info("🛑 Server stopped by user")
    except Exception as e:
        logging.error(f"❌ Server error: {e}")
        raise

if __name__ == "__main__":
    main()
