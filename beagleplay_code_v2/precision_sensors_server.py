#!/usr/bin/env python3
"""
BeaglePlay Precision Sensors Server v3.0
Integrates with Feather S3[D] dual sensors via HTTP API
Removes all BeagleConnect Freedom dependencies
"""

import time
import threading
import logging
import requests
import json
import math
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/debian/greenhouse-precision.log'),
        logging.StreamHandler()
    ]
)

# Configuration
FEATHER_S3D_IPS = ['192.168.1.81', '192.168.1.150', '192.168.1.100', '192.168.1.101', '192.168.1.102']
FEATHER_S3D_PORT = 8080
FEATHER_S3D_TIMEOUT = 5

THERMAL_CAMERA_IPS = ['192.168.1.176', '192.168.1.100', '192.168.1.177']
THERMAL_CAMERA_TIMEOUT = 5

SERVER_PORT = 8080
SENSOR_READ_INTERVAL = 5  # seconds
LOG_INTERVAL = 300  # 5 minutes

# Data storage paths
DATA_DIR = "/media/sdcard/greenhouse-data"
CSV_FILE = os.path.join(DATA_DIR, "precision_sensor_data.csv")
JSON_FILE = os.path.join(DATA_DIR, "latest_precision_data.json")

# Global sensor data
sensor_data = {
    "feather_s3d": {
        "sht45": {"temperature": None, "humidity": None, "status": "disconnected"},
        "hdc3022": {"temperature": None, "humidity": None, "status": "disconnected"},
        "averages": {"temperature": None, "humidity": None, "vpd": None},
        "sensor_count": 0,
        "last_update": None,
        "connection_status": "disconnected"
    },
    "thermal_camera": {
        "min_temp": None,
        "max_temp": None,
        "avg_temp": None,
        "center_temp": None,
        "last_update": None,
        "connection_status": "disconnected"
    },
    "calculated": {
        "enhanced_vpd": None,
        "canopy_vpd": None,
        "air_vpd": None,
        "thermal_vpd": None
    }
}

def ensure_data_directory():
    """Ensure data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)

def fetch_feather_s3d_data():
    """Fetch sensor data from Feather S3[D] HTTP API"""
    global sensor_data
    
    for ip in FEATHER_S3D_IPS:
        try:
            url = f"http://{ip}:{FEATHER_S3D_PORT}/sensors"
            response = requests.get(url, timeout=FEATHER_S3D_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Update sensor data
                sensor_data["feather_s3d"] = {
                    "sht45": data.get("sht45", {}),
                    "hdc3022": data.get("hdc3022", {}),
                    "averages": data.get("averages", {}),
                    "sensor_count": data.get("sensor_count", 0),
                    "last_update": datetime.now().isoformat(),
                    "connection_status": "connected",
                    "feather_ip": ip,
                    "uptime": data.get("uptime", 0),
                    "free_memory": data.get("free_memory", 0)
                }
                
                logging.info(f"✅ Feather S3[D] data updated from {ip}")
                return True
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ Feather S3[D] connection failed to {ip}: {e}")
            continue
        except Exception as e:
            logging.error(f"❌ Feather S3[D] error with {ip}: {e}")
            continue
    
    # Mark as disconnected if all IPs failed
    sensor_data["feather_s3d"]["connection_status"] = "disconnected"
    sensor_data["feather_s3d"]["last_update"] = datetime.now().isoformat()
    logging.error("❌ All Feather S3[D] connections failed")
    
    # Try USB serial as fallback
    return fetch_feather_s3d_usb()

def fetch_feather_s3d_usb():
    """Fetch sensor data from Feather S3[D] via USB serial as fallback"""
    global sensor_data
    
    try:
        import serial
        import json
        
        # Try to connect to USB serial
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=2)
        
        # Read a few lines to get current data
        for _ in range(10):
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Look for JSON data
                if line.startswith('{') and 'sensor_count' in line:
                    try:
                        data = json.loads(line)
                        
                        # Update sensor data with USB data
                        sensor_data["feather_s3d"] = {
                            "sht45": data.get("sht45", {}),
                            "hdc3022": data.get("hdc3022", {}),
                            "averages": data.get("averages", {}),
                            "sensor_count": data.get("sensor_count", 0),
                            "last_update": datetime.now().isoformat(),
                            "connection_status": "connected_usb",
                            "feather_ip": "USB Serial",
                            "uptime": data.get("timestamp", 0),
                            "free_memory": 0
                        }
                        
                        ser.close()
                        logging.info("✅ Feather S3[D] data updated from USB serial")
                        return True
                        
                    except json.JSONDecodeError:
                        continue
        
        ser.close()
        logging.warning("⚠️ No valid JSON data found on USB serial")
        return False
        
    except ImportError:
        logging.error("❌ pyserial not available for USB fallback")
        return False
    except Exception as e:
        logging.warning(f"⚠️ USB serial fallback failed: {e}")
        return False

def calculate_thermal_statistics(pixel_data):
    """Calculate thermal statistics from raw pixel data, excluding negative values"""
    if not pixel_data:
        return None, None, None, None, None
    
    # Filter out negative values (faulty pixels)
    valid_pixels = [temp for temp in pixel_data if temp >= 0]
    
    if not valid_pixels:
        logging.warning("⚠️ No valid thermal pixels after filtering negatives")
        return None, None, None, None, None
    
    try:
        import statistics
        
        min_temp = min(valid_pixels)
        max_temp = max(valid_pixels)
        avg_temp = statistics.mean(valid_pixels)
        median_temp = statistics.median(valid_pixels)
        
        # Calculate mode (most frequent temperature, rounded to 0.1°C)
        rounded_pixels = [round(temp * 10) / 10 for temp in valid_pixels]
        try:
            modal_temp = statistics.mode(rounded_pixels)
        except statistics.StatisticsError:
            # No unique mode, use median instead
            modal_temp = median_temp
        
        filtered_count = len(pixel_data) - len(valid_pixels)
        if filtered_count > 0:
            logging.info(f"🔧 Filtered {filtered_count} negative pixels from {len(pixel_data)} total pixels")
        
        return min_temp, max_temp, avg_temp, modal_temp, median_temp
        
    except Exception as e:
        logging.error(f"❌ Error calculating thermal statistics: {e}")
        return None, None, None, None, None

def fetch_thermal_data():
    """Fetch thermal camera data with negative pixel filtering"""
    global sensor_data
    
    for ip in THERMAL_CAMERA_IPS:
        try:
            # First, try to get raw pixel data for proper negative filtering
            raw_url = f"http://{ip}/thermal_raw"
            try:
                raw_response = requests.get(raw_url, timeout=THERMAL_CAMERA_TIMEOUT)
                if raw_response.status_code == 200:
                    raw_data = raw_response.json()
                    pixel_data = raw_data.get("pixels", [])
                    
                    if pixel_data:
                        # Calculate statistics from raw pixels, excluding negatives
                        min_temp, max_temp, avg_temp, modal_temp, median_temp = calculate_thermal_statistics(pixel_data)
                        
                        sensor_data["thermal_camera"] = {
                            "min_temp": min_temp,
                            "max_temp": max_temp,
                            "avg_temp": avg_temp,
                            "modal_temp": modal_temp,
                            "median_temp": median_temp,
                            "last_update": datetime.now().isoformat(),
                            "connection_status": "connected",
                            "camera_ip": ip,
                            "data_source": "raw_pixels",
                            "total_pixels": len(pixel_data),
                            "negative_pixels_filtered": len(pixel_data) - len([t for t in pixel_data if t >= 0])
                        }
                        
                        logging.info(f"✅ Thermal camera data updated from raw pixels ({ip})")
                        return True
            except:
                # Raw pixel data not available, fall back to pre-calculated stats
                pass
            
            # Fallback: Use pre-calculated statistics with negative value filtering
            url = f"http://{ip}/thermal_data"
            response = requests.get(url, timeout=THERMAL_CAMERA_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter out negative temperature values (faulty pixels)
                min_temp = data.get("minTemp", None)
                max_temp = data.get("maxTemp", None)
                avg_temp = data.get("meanTemp", None)
                modal_temp = data.get("modeTemp", None)
                median_temp = data.get("medianTemp", None)
                
                # Validate and filter negative temperatures
                filtered_temps = {}
                temp_fields = {
                    "min_temp": min_temp,
                    "max_temp": max_temp, 
                    "avg_temp": avg_temp,
                    "modal_temp": modal_temp,
                    "median_temp": median_temp
                }
                
                negative_count = 0
                for field, value in temp_fields.items():
                    if value is not None:
                        if value < 0:
                            logging.warning(f"⚠️ Thermal camera negative temperature detected: {field}={value:.2f}°C (filtered out)")
                            filtered_temps[field] = None  # Filter out negative values
                            negative_count += 1
                        else:
                            filtered_temps[field] = value
                    else:
                        filtered_temps[field] = None
                
                if negative_count > 0:
                    logging.info(f"🔧 Filtered {negative_count} negative temperature values from thermal camera")
                
                sensor_data["thermal_camera"] = {
                    "min_temp": filtered_temps["min_temp"],
                    "max_temp": filtered_temps["max_temp"],
                    "avg_temp": filtered_temps["avg_temp"],
                    "modal_temp": filtered_temps["modal_temp"],
                    "median_temp": filtered_temps["median_temp"],
                    "last_update": datetime.now().isoformat(),
                    "connection_status": "connected",
                    "camera_ip": ip,
                    "data_source": "pre_calculated",
                    "negative_pixels_filtered": negative_count
                }
                
                logging.info(f"✅ Thermal camera data updated from pre-calculated stats ({ip})")
                return True
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ Thermal camera connection failed to {ip}: {e}")
            continue
        except Exception as e:
            logging.error(f"❌ Thermal camera error with {ip}: {e}")
            continue
    
    # Mark as disconnected if all IPs failed
    sensor_data["thermal_camera"]["connection_status"] = "disconnected"
    sensor_data["thermal_camera"]["last_update"] = datetime.now().isoformat()
    return False

def calculate_enhanced_vpd():
    """Calculate enhanced VPD using thermal camera data"""
    global sensor_data
    
    try:
        # Get air temperature and humidity from Feather S3[D]
        air_temp = sensor_data["feather_s3d"]["averages"].get("temperature")
        air_humidity = sensor_data["feather_s3d"]["averages"].get("humidity")
        
        # Get canopy temperature from thermal camera
        canopy_temp = sensor_data["thermal_camera"].get("avg_temp")
        
        if air_temp is None or air_humidity is None:
            sensor_data["calculated"]["enhanced_vpd"] = None
            return
        
        # Calculate air VPD
        air_svp = 0.6108 * math.exp(17.27 * air_temp / (air_temp + 237.3))
        air_avp = air_svp * (air_humidity / 100.0)
        air_vpd = air_svp - air_avp
        
        sensor_data["calculated"]["air_vpd"] = round(air_vpd, 2)
        
        # Calculate canopy VPD if thermal data available
        if canopy_temp is not None:
            canopy_svp = 0.6108 * math.exp(17.27 * canopy_temp / (canopy_temp + 237.3))
            canopy_vpd = canopy_svp - air_avp  # Use air humidity for canopy VPD
            thermal_vpd = canopy_svp - canopy_svp * (air_humidity / 100.0)
            
            sensor_data["calculated"]["canopy_vpd"] = round(canopy_vpd, 2)
            sensor_data["calculated"]["thermal_vpd"] = round(thermal_vpd, 2)
            sensor_data["calculated"]["enhanced_vpd"] = round((air_vpd + canopy_vpd) / 2, 2)
        else:
            sensor_data["calculated"]["enhanced_vpd"] = air_vpd
            sensor_data["calculated"]["canopy_vpd"] = None
            sensor_data["calculated"]["thermal_vpd"] = None
        
    except Exception as e:
        logging.error(f"❌ Enhanced VPD calculation error: {e}")
        sensor_data["calculated"]["enhanced_vpd"] = None

def log_data():
    """Log sensor data to CSV and JSON files"""
    try:
        ensure_data_directory()
        
        # Prepare data row
        timestamp = datetime.now().isoformat()
        
        # Feather S3[D] data
        sht45_temp = sensor_data["feather_s3d"]["sht45"].get("temperature")
        sht45_humidity = sensor_data["feather_s3d"]["sht45"].get("humidity")
        hdc3022_temp = sensor_data["feather_s3d"]["hdc3022"].get("temperature")
        hdc3022_humidity = sensor_data["feather_s3d"]["hdc3022"].get("humidity")
        avg_temp = sensor_data["feather_s3d"]["averages"].get("temperature")
        avg_humidity = sensor_data["feather_s3d"]["averages"].get("humidity")
        avg_vpd = sensor_data["feather_s3d"]["averages"].get("vpd")
        
        # Thermal camera data
        thermal_min = sensor_data["thermal_camera"].get("min_temp")
        thermal_max = sensor_data["thermal_camera"].get("max_temp")
        thermal_avg = sensor_data["thermal_camera"].get("avg_temp")
        thermal_modal = sensor_data["thermal_camera"].get("modal_temp")
        
        # Enhanced VPD data
        enhanced_vpd = sensor_data["calculated"].get("enhanced_vpd")
        air_vpd = sensor_data["calculated"].get("air_vpd")
        canopy_vpd = sensor_data["calculated"].get("canopy_vpd")
        thermal_vpd = sensor_data["calculated"].get("thermal_vpd")
        
        # CSV logging
        csv_row = [
            timestamp,
            sht45_temp, sht45_humidity,
            hdc3022_temp, hdc3022_humidity,
            avg_temp, avg_humidity, avg_vpd,
            thermal_min, thermal_max, thermal_avg, thermal_modal,
            enhanced_vpd, air_vpd, canopy_vpd, thermal_vpd
        ]
        
        # Write CSV header if file doesn't exist
        if not os.path.exists(CSV_FILE):
            header = [
                "timestamp",
                "sht45_temp", "sht45_humidity",
                "hdc3022_temp", "hdc3022_humidity", 
                "avg_temp", "avg_humidity", "avg_vpd",
                "thermal_min", "thermal_max", "thermal_avg", "thermal_modal",
                "enhanced_vpd", "air_vpd", "canopy_vpd", "thermal_vpd"
            ]
            with open(CSV_FILE, 'w') as f:
                f.write(','.join(header) + '\n')
        
        # Append data
        with open(CSV_FILE, 'a') as f:
            f.write(','.join(str(x) if x is not None else '' for x in csv_row) + '\n')
        
        # JSON logging (latest data)
        with open(JSON_FILE, 'w') as f:
            json.dump(sensor_data, f, indent=2)
        
        logging.info(f"📊 Data logged: {len([x for x in csv_row[1:] if x is not None])} values")
        
    except Exception as e:
        logging.error(f"❌ Data logging error: {e}")

def sensor_update_loop():
    """Main sensor update loop"""
    last_log_time = 0
    
    while True:
        try:
            # Fetch sensor data
            fetch_feather_s3d_data()
            fetch_thermal_data()
            calculate_enhanced_vpd()
            
            # Log data at specified interval
            current_time = time.time()
            if current_time - last_log_time >= LOG_INTERVAL:
                log_data()
                last_log_time = current_time
            
            time.sleep(SENSOR_READ_INTERVAL)
            
        except Exception as e:
            logging.error(f"❌ Sensor update loop error: {e}")
            time.sleep(5)

class PrecisionSensorHandler(BaseHTTPRequestHandler):
    """HTTP request handler for precision sensor server"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/':
                self.serve_dashboard()
            elif path == '/api/sensors':
                self.serve_sensor_data()
            elif path == '/api/health':
                self.serve_health_check()
            elif path == '/download/csv':
                self.serve_csv_download()
            elif path == '/export_data':
                self.serve_csv_download()
            elif path == '/plots':
                self.serve_plots_page()
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            logging.error(f"❌ HTTP handler error: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_dashboard(self):
        """Serve the main HTML dashboard"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Get current sensor data
        sht45_temp = sensor_data["feather_s3d"]["sht45"]["temperature"] or 0.0
        sht45_humidity = sensor_data["feather_s3d"]["sht45"]["humidity"] or 0.0
        hdc3022_temp = sensor_data["feather_s3d"]["hdc3022"]["temperature"] or 0.0
        hdc3022_humidity = sensor_data["feather_s3d"]["hdc3022"]["humidity"] or 0.0
        avg_temp = sensor_data["feather_s3d"]["averages"]["temperature"] or 0.0
        avg_humidity = sensor_data["feather_s3d"]["averages"]["humidity"] or 0.0
        avg_vpd = sensor_data["feather_s3d"]["averages"]["vpd"] or 0.0
        
        # Thermal camera data
        thermal_min = sensor_data["thermal_camera"]["min_temp"] or 0.0
        thermal_max = sensor_data["thermal_camera"]["max_temp"] or 0.0
        thermal_avg = sensor_data["thermal_camera"]["avg_temp"] or 0.0
        thermal_modal = sensor_data["thermal_camera"]["modal_temp"] or 0.0
        thermal_filtered_pixels = sensor_data["thermal_camera"].get("negative_pixels_filtered", 0)
        thermal_data_source = sensor_data["thermal_camera"].get("data_source", "unknown")
        thermal_total_pixels = sensor_data["thermal_camera"].get("total_pixels", 0)
        
        # Enhanced VPD calculations using thermal data with individual sensor humidity
        # Max Canopy Temperature VPD calculations
        enhanced_vpd_max_sht45 = self.calculate_vpd(thermal_max, sht45_humidity) if thermal_max and sht45_humidity else 0.0
        enhanced_vpd_max_hdc3022 = self.calculate_vpd(thermal_max, hdc3022_humidity) if thermal_max and hdc3022_humidity else 0.0
        enhanced_vpd_max_avg = self.calculate_vpd(thermal_max, avg_humidity) if thermal_max and avg_humidity else 0.0
        
        # Average Canopy Temperature VPD calculations
        enhanced_vpd_avg_sht45 = self.calculate_vpd(thermal_avg, sht45_humidity) if thermal_avg and sht45_humidity else 0.0
        enhanced_vpd_avg_hdc3022 = self.calculate_vpd(thermal_avg, hdc3022_humidity) if thermal_avg and hdc3022_humidity else 0.0
        enhanced_vpd_avg_avg = self.calculate_vpd(thermal_avg, avg_humidity) if thermal_avg and avg_humidity else 0.0
        
        # Modal Canopy Temperature VPD calculations
        enhanced_vpd_modal_sht45 = self.calculate_vpd(thermal_modal, sht45_humidity) if thermal_modal and sht45_humidity else 0.0
        enhanced_vpd_modal_hdc3022 = self.calculate_vpd(thermal_modal, hdc3022_humidity) if thermal_modal and hdc3022_humidity else 0.0
        enhanced_vpd_modal_avg = self.calculate_vpd(thermal_modal, avg_humidity) if thermal_modal and avg_humidity else 0.0
        
        # Connection status
        feather_status = sensor_data["feather_s3d"]["connection_status"]
        thermal_status = sensor_data["thermal_camera"]["connection_status"]
        sensor_count = sensor_data["feather_s3d"]["sensor_count"]
        
        # Current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Feather S3[D] Dual Sensor Dashboard</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                /* Dark mode theme */
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #121212; 
                    color: #e0e0e0; 
                }}
                
                /* Header styling */
                .header {{ 
                    background-color: #1e1e1e; 
                    padding: 15px 20px; 
                    border-radius: 5px; 
                    margin-bottom: 20px; 
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); 
                    text-align: center;
                    position: relative;
                }}
                
                /* Tools dropdown menu */
                .tools-menu {{
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
                    color: #ffffff; 
                    margin: 0; 
                    padding: 0; 
                }}
                
                h2 {{ 
                    color: #ffffff; 
                    margin-top: 0; 
                }}
                
                /* Timestamp header styling */
                .timestamp-header {{ 
                    color: #4caf50; 
                    font-style: italic; 
                    margin: 10px 0 0 0; 
                    font-size: 16px; 
                    font-weight: normal; 
                }}
                
                /* Dashboard container for landscape layout */
                .dashboard-container {{ 
                    display: flex; 
                    flex-wrap: wrap; 
                    justify-content: space-between; 
                    gap: 20px;
                }}
                
                /* Sensor box styling */
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
                
                /* Sensor value styling */
                .sensor-value {{ 
                    font-size: 28px; 
                    font-weight: bold; 
                    color: #4caf50; 
                    margin-top: 10px; 
                    text-align: center; 
                }}
                
                /* Status indicators */
                .status-connected {{ color: #4caf50; }}
                .status-disconnected {{ color: #f44336; }}
                

                
                /* Responsive adjustments */
                @media (max-width: 768px) {{ 
                    .dashboard-container {{ 
                        flex-direction: column; 
                    }}
                    .sensor-box {{ 
                        margin-bottom: 15px; 
                    }}

                }}
            </style>
        </head>
        <body>
            <div class="header">
                <!-- Tools Dropdown Menu -->
                <div class="tools-menu">
                    <button class="tools-button" onclick="toggleToolsMenu()">Tools &#9662;</button>
                    <div class="tools-dropdown" id="toolsDropdown">
                        <a href="#" onclick="showHelp(); closeToolsMenu(); return false;">Help</a>
                        <a href="/export_data" target="_blank" onclick="closeToolsMenu()">Export Logging Data</a>
                        <a href="http://192.168.1.176/" target="_blank" onclick="closeToolsMenu()">Thermal Camera</a>
                        <a href="/plots" target="_blank" onclick="closeToolsMenu()">Time Series Plots</a>
                    </div>
                </div>
                
                <h1>Feather S3[D] Dual Sensor Dashboard</h1>
                <div class="timestamp-header">Last Updated: {current_time}</div>
                <div style="margin-top: 10px; font-size: 14px;">
                    Feather S3[D]: <span class="{'status-connected' if feather_status == 'connected' else 'status-disconnected'}">{feather_status}</span> | 
                    Sensors: {sensor_count}/2 | 
                    Thermal Camera: <span class="{'status-connected' if thermal_status == 'connected' else 'status-disconnected'}">{thermal_status}</span>
                </div>
            </div>
            
            <h2 style="color: #4caf50; text-align: center; margin: 20px 0;">Individual Sensor Readings</h2>
            <div class="dashboard-container">
                <div class="sensor-box">
                    <h2>SHT45 Temperature</h2>
                    <div class="sensor-value">{sht45_temp:.1f} &deg;C</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        High-precision sensor
                    </div>
                </div>
                
                <div class="sensor-box">
                    <h2>SHT45 Humidity</h2>
                    <div class="sensor-value">{sht45_humidity:.1f} %RH</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        High-precision sensor
                    </div>
                </div>
                
                <div class="sensor-box">
                    <h2>HDC3022 Temperature</h2>
                    <div class="sensor-value">{hdc3022_temp:.1f} &deg;C</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        High-precision sensor
                    </div>
                </div>
                
                <div class="sensor-box">
                    <h2>HDC3022 Humidity</h2>
                    <div class="sensor-value">{hdc3022_humidity:.1f} %RH</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        High-precision sensor
                    </div>
                </div>
            </div>
            
            <h2 style="color: #2196f3; text-align: center; margin: 20px 0;">Averaged Sensor Data</h2>
            <div class="dashboard-container">
                <div class="sensor-box" style="background-color: #1a237e;">
                    <h2>Average Temperature</h2>
                    <div class="sensor-value" style="color: #2196f3">{avg_temp:.1f} &deg;C</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Mean of both sensors
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #1a237e;">
                    <h2>Average Humidity</h2>
                    <div class="sensor-value" style="color: #2196f3">{avg_humidity:.1f} %RH</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Mean of both sensors
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #1a237e;">
                    <h2>Standard VPD</h2>
                    <div class="sensor-value" style="color: #2196f3">{avg_vpd:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Using averaged air temperature
                    </div>
                </div>
            </div>
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Enhanced VPD (Max Canopy Temperature)</h2>
            <div class="dashboard-container">
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Max + SHT45)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_max_sht45:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Max: {thermal_max:.1f}&deg;C<br>
                        Humidity: SHT45 ({sht45_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Max + HDC3022)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_max_hdc3022:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Max: {thermal_max:.1f}&deg;C<br>
                        Humidity: HDC3022 ({hdc3022_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Max + Average)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_max_avg:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Max: {thermal_max:.1f}&deg;C<br>
                        Humidity: Average ({avg_humidity:.1f}%RH)
                    </div>
                </div>
            </div>
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Enhanced VPD (Average Canopy Temperature)</h2>
            <div class="dashboard-container">
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Avg + SHT45)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_avg_sht45:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Avg: {thermal_avg:.1f}&deg;C<br>
                        Humidity: SHT45 ({sht45_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Avg + HDC3022)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_avg_hdc3022:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Avg: {thermal_avg:.1f}&deg;C<br>
                        Humidity: HDC3022 ({hdc3022_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Avg + Average)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_avg_avg:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Avg: {thermal_avg:.1f}&deg;C<br>
                        Humidity: Average ({avg_humidity:.1f}%RH)
                    </div>
                </div>
            </div>
            
            <h2 style="color: #ff9800; text-align: center; margin: 20px 0;">Enhanced VPD (Modal Canopy Temperature)</h2>
            <div class="dashboard-container">
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Modal + SHT45)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_modal_sht45:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Modal: {thermal_modal:.1f}&deg;C<br>
                        Humidity: SHT45 ({sht45_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Modal + HDC3022)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_modal_hdc3022:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Modal: {thermal_modal:.1f}&deg;C<br>
                        Humidity: HDC3022 ({hdc3022_humidity:.1f}%RH)
                    </div>
                </div>
                
                <div class="sensor-box" style="background-color: #2d1b00;">
                    <h2>VPD (Modal + Average)</h2>
                    <div class="sensor-value" style="color: #ff9800">{enhanced_vpd_modal_avg:.2f} kPa</div>
                    <div style="color: #888; font-size: 12px; text-align: center; margin-top: 5px;">
                        Thermal Modal: {thermal_modal:.1f}&deg;C<br>
                        Humidity: Average ({avg_humidity:.1f}%RH)
                    </div>
                </div>
            </div>
            
            <h2 style="color: #4caf50; text-align: center; margin: 20px 0;">Thermal Camera Statistics</h2>
            <div class="dashboard-container">
                <div class="sensor-box">
                    <h2>Min Temperature</h2>
                    <div class="sensor-value">{thermal_min:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Max Temperature</h2>
                    <div class="sensor-value">{thermal_max:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Average Temperature</h2>
                    <div class="sensor-value">{thermal_avg:.1f} &deg;C</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Modal Temperature</h2>
                    <div class="sensor-value">{thermal_modal:.1f} &deg;C</div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #888; font-size: 12px;">
                <p><strong>Data Source:</strong> {thermal_data_source.replace('_', ' ').title()}</p>
                {f'<p><strong>Pixel Filtering:</strong> {thermal_filtered_pixels} negative pixels filtered' + (f' out of {thermal_total_pixels} total' if thermal_total_pixels > 0 else '') + '</p>' if thermal_filtered_pixels > 0 else '<p><strong>Pixel Quality:</strong> All pixels valid (no negative values detected)</p>'}
            </div>
            
            <div style="text-align: center; margin-top: 30px; color: #888; font-size: 14px;">
                <p>Feather S3[D] Dual Sensor System | Enhanced by Windsurf AI | BeagleBoard.org Foundation</p>
                <p>Auto-refresh: 10 seconds</p>
            </div>
            
            <!-- Help Modal -->
            <div id="helpModal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8);">
                <div style="background-color: #1e1e1e; margin: 5% auto; padding: 20px; border-radius: 10px; width: 80%; max-width: 800px; color: #e0e0e0; max-height: 80%; overflow-y: auto;">
                    <span onclick="closeHelp()" style="color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>
                    <h2 style="color: #4caf50; margin-top: 0;">VPD Calculations & Dashboard Help</h2>
                    
                    <h3 style="color: #ff9800;">Vapor Pressure Deficit (VPD) Explained</h3>
                    <p><strong>VPD</strong> measures the difference between the moisture currently in the air and how much moisture the air can hold when saturated. It's crucial for plant transpiration and growth.</p>
                    
                    <h4 style="color: #4caf50;">VPD Calculation Formula:</h4>
                    <div style="background-color: #2d2d2d; padding: 15px; border-radius: 5px; font-family: monospace;">
                        <strong>SVP</strong> = 0.6108 &times; e^(17.27 &times; T / (T + 237.3)) <em style="color: #888;">(Tetens Equation or Magnus-Tetens formula)</em><br>
                        <strong>AVP</strong> = SVP &times; (RH / 100)<br>
                        <strong>VPD</strong> = SVP - AVP<br><br>
                        Where:<br>
                        &bull; SVP = Saturation Vapor Pressure (kPa)<br>
                        &bull; AVP = Actual Vapor Pressure (kPa)<br>
                        &bull; T = Temperature (&deg;C)<br>
                        &bull; RH = Relative Humidity (%)
                    </div>
                    
                    <h4 style="color: #4caf50;">Enhanced VPD Types:</h4>
                    <ul>
                        <li><strong>Enhanced VPD (Dashboard):</strong> Uses thermal camera temperature (Max/Avg/Modal) + individual sensor humidity (SHT45 or HDC3022)</li>
                        <li><strong>Enhanced VPD (Plot 1):</strong> Average of Air VPD + Canopy VPD (uses averaged sensor data + thermal average)</li>
                        <li><strong>Canopy VPD (Plot 2):</strong> Thermal camera temperature + air humidity (leaf temperature effect)</li>
                        <li><strong>Thermal VPD (Plot 3):</strong> Thermal camera temperature + thermal-derived humidity (pure thermal calculation)</li>
                    </ul>
                    
                    <h4 style="color: #4caf50;">VPD Calculation Details:</h4>
                    <ul>
                        <li><strong>Air VPD:</strong> Uses averaged air temperature + averaged air humidity from both sensors</li>
                        <li><strong>Canopy VPD:</strong> Uses thermal camera temperature + air humidity (simulates leaf temperature)</li>
                        <li><strong>Thermal VPD:</strong> Uses thermal camera temperature + thermal-calculated humidity</li>
                    </ul>
                    
                    <h4 style="color: #4caf50;">Optimal VPD Ranges:</h4>
                    <ul>
                        <li><strong>0.4-0.8 kPa:</strong> Seedlings and clones</li>
                        <li><strong>0.8-1.2 kPa:</strong> Vegetative growth</li>
                        <li><strong>1.0-1.5 kPa:</strong> Flowering stage</li>
                    </ul>
                    
                    <h3 style="color: #ff9800;">Tools Menu Options:</h3>
                    <ul>
                        <li><strong>Help:</strong> This information dialog with VPD explanations</li>
                        <li><strong>Export Data:</strong> Download all logged sensor data as CSV file for analysis in Excel or other tools</li>
                        <li><strong>Thermal Camera:</strong> View live thermal imaging heat map from ESP32-S3 camera</li>
                        <li><strong>Time Series Plots:</strong> Interactive real-time XY plots with time on X-axis showing all sensor readings</li>
                    </ul>
                    
                    <h3 style="color: #ff9800;">System Information:</h3>
                    <ul>
                        <li><strong>Sensors:</strong> SHT45 + HDC3022 dual high-precision sensors</li>
                        <li><strong>Connectivity:</strong> WiFi HTTP API + USB Serial fallback</li>
                        <li><strong>Data Logging:</strong> Automatic CSV/JSON logging to SD card</li>
                        <li><strong>Update Rate:</strong> 10-second auto-refresh</li>
                    </ul>
                </div>
            </div>
            
            <script>
                // Global variables
                let refreshTimer;
                let helpModalOpen = false;
                
                // Auto-refresh function
                function startAutoRefresh() {{
                    if (!helpModalOpen) {{
                        refreshTimer = setTimeout(function() {{
                            location.reload();
                        }}, 10000);
                    }}
                }}
                
                // Tools menu functions
                function toggleToolsMenu() {{
                    var dropdown = document.getElementById('toolsDropdown');
                    dropdown.classList.toggle('show');
                }}
                
                function closeToolsMenu() {{
                    var dropdown = document.getElementById('toolsDropdown');
                    dropdown.classList.remove('show');
                }}
                
                // Help modal functions
                function showHelp() {{
                    var modal = document.getElementById('helpModal');
                    modal.style.display = 'block';
                    helpModalOpen = true;
                    // Stop auto-refresh completely while help is open
                    clearTimeout(refreshTimer);
                    // Prevent any background refresh attempts
                    clearInterval(window.refreshInterval);
                }}
                
                function closeHelp() {{
                    var modal = document.getElementById('helpModal');
                    modal.style.display = 'none';
                    helpModalOpen = false;
                    // Resume auto-refresh
                    startAutoRefresh();
                }}
                
                // Event handlers
                document.addEventListener('click', function(event) {{
                    var dropdown = document.getElementById('toolsDropdown');
                    var toolsButton = document.querySelector('.tools-button');
                    
                    // Close tools dropdown when clicking outside
                    if (!toolsButton.contains(event.target) && !dropdown.contains(event.target)) {{
                        closeToolsMenu();
                    }}
                }});
                
                // Help modal click handler - ONLY closes on X button click
                document.addEventListener('click', function(event) {{
                    if (!helpModalOpen) return;
                    
                    var modal = document.getElementById('helpModal');
                    var modalContent = modal.querySelector('div');
                    var closeButton = modal.querySelector('span[onclick="closeHelp()"]');
                    
                    // Only close if clicking the X button specifically
                    if (event.target === closeButton) {{
                        closeHelp();
                        return;
                    }}
                    
                    // Prevent modal from closing when clicking inside modal content
                    if (modalContent && modalContent.contains(event.target)) {{
                        event.stopPropagation();
                        return;
                    }}
                    
                    // Don't close when clicking on modal background
                    event.stopPropagation();
                }});
                
                // Add escape key handler for Help modal
                document.addEventListener('keydown', function(event) {{
                    if (event.key === 'Escape' && helpModalOpen) {{
                        closeHelp();
                    }}
                }});
                
                // Start auto-refresh
                startAutoRefresh();
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def calculate_vpd(self, temperature, humidity):
        """Calculate Vapor Pressure Deficit"""
        if not temperature or not humidity:
            return 0.0
        
        # Saturation vapor pressure (kPa)
        svp = 0.6108 * math.exp(17.27 * temperature / (temperature + 237.3))
        # Actual vapor pressure
        avp = humidity / 100.0 * svp
        # VPD
        vpd = svp - avp
        return max(0.0, vpd)
    
    def serve_sensor_data(self):
        """Serve current sensor data"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps(sensor_data, indent=2).encode())
    
    def serve_health_check(self):
        """Serve health check"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "healthy",
            "feather_s3d_connected": sensor_data["feather_s3d"]["connection_status"] == "connected",
            "thermal_camera_connected": sensor_data["thermal_camera"]["connection_status"] == "connected",
            "sensors_working": sensor_data["feather_s3d"]["sensor_count"],
            "data_logging": os.path.exists(CSV_FILE),
            "uptime": time.time()
        }
        
        self.wfile.write(json.dumps(health_data, indent=2).encode())
    
    def serve_csv_download(self):
        """Serve CSV data download"""
        if os.path.exists(CSV_FILE):
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header('Content-Disposition', 'attachment; filename="precision_sensor_data.csv"')
            self.end_headers()
            
            with open(CSV_FILE, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "CSV file not found")
    
    def serve_plots_page(self):
        """Serve real-time plots page"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Greenhouse Monitoring - Time Series Plots</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
                
                h1 {{
                    color: #ffffff;
                    margin: 0;
                }}
                
                .plot-container {{
                    background-color: #1e1e1e;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                
                .plot-title {{
                    color: #4caf50;
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    text-align: center;
                }}
                
                .back-button {{
                    background-color: #4caf50;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin-bottom: 20px;
                    transition: background-color 0.3s;
                }}
                
                .back-button:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Real-Time Greenhouse Monitoring Plots</h1>
                <a href="/" class="back-button">&larr; Back to Dashboard</a>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Temperature Readings</div>
                <div id="tempPlot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Humidity Readings</div>
                <div id="humidityPlot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">VPD Calculations</div>
                <div id="vpdPlot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Thermal Camera Temperatures</div>
                <div id="thermalPlot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Enhanced VPD (Average of Air VPD + Canopy VPD)</div>
                <div id="enhancedVpdSht45Plot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Canopy VPD (Thermal Camera Temp + Air Humidity)</div>
                <div id="enhancedVpdHdc3022Plot" style="height: 400px;"></div>
            </div>
            
            <div class="plot-container">
                <div class="plot-title">Thermal VPD (Thermal Camera Temp + Thermal Humidity)</div>
                <div id="thermalVpdPlot" style="height: 400px;"></div>
            </div>
            
            <script>
                // Dark theme configuration for Plotly
                const darkTheme = {{
                    paper_bgcolor: '#1e1e1e',
                    plot_bgcolor: '#2d2d2d',
                    font: {{ color: '#e0e0e0' }},
                    xaxis: {{
                        gridcolor: '#444',
                        zerolinecolor: '#666',
                        tickcolor: '#e0e0e0',
                        linecolor: '#666'
                    }},
                    yaxis: {{
                        gridcolor: '#444',
                        zerolinecolor: '#666',
                        tickcolor: '#e0e0e0',
                        linecolor: '#666'
                    }}
                }};
                
                // VPD calculation function
                function calculateVPD(temperature, humidity) {{
                    if (temperature <= 0 || humidity <= 0) return 0;
                    
                    // Calculate saturation vapor pressure (SVP) using Magnus formula
                    var svp = 0.6108 * Math.exp((17.27 * temperature) / (temperature + 237.3));
                    
                    // Calculate actual vapor pressure (AVP)
                    var avp = (humidity / 100) * svp;
                    
                    // VPD = SVP - AVP
                    var vpd = svp - avp;
                    
                    return Math.round(vpd * 100) / 100; // Round to 2 decimal places
                }}
                
                // Initialize empty data arrays
                let timestamps = [];
                let sht45Temp = [], hdc3022Temp = [], avgTemp = [];
                let sht45Humidity = [], hdc3022Humidity = [], avgHumidity = [];
                let sht45VPD = [], hdc3022VPD = [], avgVPD = [];
                let thermalMin = [], thermalMax = [], thermalAvg = [], thermalModal = [];
                let enhancedVpdSht45 = [], enhancedVpdHdc3022 = [], thermalVpd = [];
                
                // Fetch and update data
                async function updatePlots() {{
                    try {{
                        const response = await fetch('/api/sensors');
                        const data = await response.json();
                        
                        // Add timestamp
                        const now = new Date();
                        timestamps.push(now);
                        
                        // Add sensor data
                        sht45Temp.push(data.feather_s3d.sht45.temperature || 0);
                        hdc3022Temp.push(data.feather_s3d.hdc3022.temperature || 0);
                        avgTemp.push(data.feather_s3d.averages.temperature || 0);
                        
                        sht45Humidity.push(data.feather_s3d.sht45.humidity || 0);
                        hdc3022Humidity.push(data.feather_s3d.hdc3022.humidity || 0);
                        avgHumidity.push(data.feather_s3d.averages.humidity || 0);
                        
                        // Calculate individual VPD values since they're not provided by API
                        var sht45_vpd = calculateVPD(data.feather_s3d.sht45.temperature || 0, data.feather_s3d.sht45.humidity || 0);
                        var hdc3022_vpd = calculateVPD(data.feather_s3d.hdc3022.temperature || 0, data.feather_s3d.hdc3022.humidity || 0);
                        
                        sht45VPD.push(sht45_vpd);
                        hdc3022VPD.push(hdc3022_vpd);
                        avgVPD.push(data.feather_s3d.averages.vpd || 0);
                        
                        thermalMin.push(data.thermal_camera.min_temp || 0);
                        thermalMax.push(data.thermal_camera.max_temp || 0);
                        thermalAvg.push(data.thermal_camera.avg_temp || 0);
                        thermalModal.push(data.thermal_camera.modal_temp || 0);
                        
                        // Enhanced VPD calculations
                        enhancedVpdSht45.push(data.calculated?.enhanced_vpd || 0);
                        enhancedVpdHdc3022.push(data.calculated?.canopy_vpd || 0);
                        thermalVpd.push(data.calculated?.thermal_vpd || 0);
                        
                        // Keep only last 100 points
                        if (timestamps.length > 100) {{
                            timestamps = timestamps.slice(-100);
                            sht45Temp = sht45Temp.slice(-100);
                            hdc3022Temp = hdc3022Temp.slice(-100);
                            avgTemp = avgTemp.slice(-100);
                            sht45Humidity = sht45Humidity.slice(-100);
                            hdc3022Humidity = hdc3022Humidity.slice(-100);
                            avgHumidity = avgHumidity.slice(-100);
                            sht45VPD = sht45VPD.slice(-100);
                            hdc3022VPD = hdc3022VPD.slice(-100);
                            avgVPD = avgVPD.slice(-100);
                            thermalMin = thermalMin.slice(-100);
                            thermalMax = thermalMax.slice(-100);
                            thermalAvg = thermalAvg.slice(-100);
                            thermalModal = thermalModal.slice(-100);
                            enhancedVpdSht45 = enhancedVpdSht45.slice(-100);
                            enhancedVpdHdc3022 = enhancedVpdHdc3022.slice(-100);
                            thermalVpd = thermalVpd.slice(-100);
                        }}
                        
                        // Update plots
                        updateTemperaturePlot();
                        updateHumidityPlot();
                        updateVPDPlot();
                        updateThermalPlot();
                        updateEnhancedVpdSht45Plot();
                        updateEnhancedVpdHdc3022Plot();
                        updateThermalVpdPlot();
                        
                    }} catch (error) {{
                        console.error('Error fetching data:', error);
                    }}
                }}
                
                function updateTemperaturePlot() {{
                    const traces = [
                        {{ x: timestamps, y: sht45Temp, name: 'SHT45', line: {{ color: '#4caf50' }} }},
                        {{ x: timestamps, y: hdc3022Temp, name: 'HDC3022', line: {{ color: '#2196f3' }} }},
                        {{ x: timestamps, y: avgTemp, name: 'Average', line: {{ color: '#ff9800' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Temperature (&deg;C)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'Temperature (&deg;C)' }}
                    }};
                    
                    Plotly.newPlot('tempPlot', traces, layout, {{ responsive: true }});
                }}
                
                function updateHumidityPlot() {{
                    const traces = [
                        {{ x: timestamps, y: sht45Humidity, name: 'SHT45', line: {{ color: '#4caf50' }} }},
                        {{ x: timestamps, y: hdc3022Humidity, name: 'HDC3022', line: {{ color: '#2196f3' }} }},
                        {{ x: timestamps, y: avgHumidity, name: 'Average', line: {{ color: '#ff9800' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Relative Humidity (%)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'Humidity (%)' }}
                    }};
                    
                    Plotly.newPlot('humidityPlot', traces, layout, {{ responsive: true }});
                }}
                
                function updateVPDPlot() {{
                    const traces = [
                        {{ x: timestamps, y: sht45VPD, name: 'SHT45 VPD', line: {{ color: '#4caf50' }} }},
                        {{ x: timestamps, y: hdc3022VPD, name: 'HDC3022 VPD', line: {{ color: '#2196f3' }} }},
                        {{ x: timestamps, y: avgVPD, name: 'Average VPD', line: {{ color: '#ff9800' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Vapor Pressure Deficit (kPa)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'VPD (kPa)' }}
                    }};
                    
                    Plotly.newPlot('vpdPlot', traces, layout, {{ responsive: true }});
                }}
                
                function updateThermalPlot() {{
                    const traces = [
                        {{ x: timestamps, y: thermalMin, name: 'Min Temp', line: {{ color: '#9c27b0' }} }},
                        {{ x: timestamps, y: thermalMax, name: 'Max Temp', line: {{ color: '#f44336' }} }},
                        {{ x: timestamps, y: thermalAvg, name: 'Avg Temp', line: {{ color: '#ff9800' }} }},
                        {{ x: timestamps, y: thermalModal, name: 'Modal Temp', line: {{ color: '#00bcd4' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Thermal Camera Temperatures (&deg;C)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'Temperature (&deg;C)' }}
                    }};
                    
                    Plotly.newPlot('thermalPlot', traces, layout, {{ responsive: true }});
                }}
                
                function updateEnhancedVpdSht45Plot() {{
                    const traces = [
                        {{ x: timestamps, y: enhancedVpdSht45, name: 'Enhanced VPD (Air + Canopy Average)', line: {{ color: '#e91e63' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Enhanced VPD (Average of Air VPD + Canopy VPD) (kPa)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'VPD (kPa)' }}
                    }};
                    
                    Plotly.newPlot('enhancedVpdSht45Plot', traces, layout, {{ responsive: true }});
                }}
                
                function updateEnhancedVpdHdc3022Plot() {{
                    const traces = [
                        {{ x: timestamps, y: enhancedVpdHdc3022, name: 'Canopy VPD (Thermal Temp + Air Humidity)', line: {{ color: '#673ab7' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Canopy VPD (Thermal Camera Temp + Air Humidity) (kPa)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'VPD (kPa)' }}
                    }};
                    
                    Plotly.newPlot('enhancedVpdHdc3022Plot', traces, layout, {{ responsive: true }});
                }}
                
                function updateThermalVpdPlot() {{
                    const traces = [
                        {{ x: timestamps, y: thermalVpd, name: 'Thermal VPD (Thermal Temp + Thermal Humidity)', line: {{ color: '#ff5722' }} }}
                    ];
                    
                    const layout = {{
                        ...darkTheme,
                        title: 'Thermal VPD (Thermal Camera Temp + Thermal Humidity) (kPa)',
                        xaxis: {{ ...darkTheme.xaxis, title: 'Time' }},
                        yaxis: {{ ...darkTheme.yaxis, title: 'VPD (kPa)' }}
                    }};
                    
                    Plotly.newPlot('thermalVpdPlot', traces, layout, {{ responsive: true }});
                }}
                
                // Initialize plots and start updating
                updatePlots();
                setInterval(updatePlots, 5000); // Update every 5 seconds
            </script>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())

def main():
    """Main server function"""
    logging.info("🌱 Starting Precision Sensors Server v3.0")
    
    # Ensure data directory exists
    ensure_data_directory()
    
    # Start sensor update thread
    sensor_thread = threading.Thread(target=sensor_update_loop, daemon=True)
    sensor_thread.start()
    logging.info("✅ Sensor update thread started")
    
    # Start HTTP server
    server = HTTPServer(('0.0.0.0', SERVER_PORT), PrecisionSensorHandler)
    logging.info(f"🚀 HTTP server starting on port {SERVER_PORT}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("🛑 Server stopped by user")
    except Exception as e:
        logging.error(f"❌ Server error: {e}")
    finally:
        server.shutdown()
        logging.info("👋 Precision Sensors Server stopped")

if __name__ == "__main__":
    main()
