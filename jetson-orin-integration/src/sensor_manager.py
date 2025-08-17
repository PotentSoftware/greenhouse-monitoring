#!/usr/bin/env python3
"""
Sensor Manager for Jetson Orin Nano
Handles communication with Feather S3[D] and tCam-Mini
"""

import requests
import socket
import json
import base64
import numpy as np
import logging
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

class SensorManager:
    def __init__(self, config):
        self.config = config
        self.feather_ips = config.FEATHER_S3D_IPS
        self.feather_port = config.FEATHER_S3D_PORT
        self.feather_timeout = config.FEATHER_S3D_TIMEOUT
        
        self.tcam_host = config.TCAM_HOST
        self.tcam_port = config.TCAM_PORT
        self.tcam_timeout = config.TCAM_TIMEOUT
        
        self.thermal_resolution = config.THERMAL_RESOLUTION
        self.kelvin_offset = config.KELVIN_OFFSET
        
        # Initialize sensor data structure
        self.sensor_data = {
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
                "modal_temp": None,
                "median_temp": None,
                "last_update": None,
                "connection_status": "disconnected",
                "raw_image": None,
                "stats": {}
            }
        }
        
        logging.info("🚀 Sensor Manager initialized for Jetson Orin Nano")
    
    def fetch_feather_s3d_data(self) -> bool:
        """Fetch sensor data from Feather S3[D] HTTP API"""
        for ip in self.feather_ips:
            try:
                url = f"http://{ip}:{self.feather_port}/sensors"
                response = requests.get(url, timeout=self.feather_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Update sensor data
                    self.sensor_data["feather_s3d"] = {
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
        self.sensor_data["feather_s3d"]["connection_status"] = "disconnected"
        self.sensor_data["feather_s3d"]["last_update"] = datetime.now().isoformat()
        logging.error("❌ All Feather S3[D] connections failed")
        return False
    
    def connect_tcam_and_send(self, command: Dict) -> Optional[Dict]:
        """Connect to tCam-Mini and send command"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.tcam_timeout)
            sock.connect((self.tcam_host, self.tcam_port))
            
            # Send command with STX/ETX delimiters
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
            logging.error(f"❌ tCam communication error: {e}")
            return None
    
    def raw_to_celsius(self, raw_data: np.ndarray) -> np.ndarray:
        """Convert raw Lepton thermal data to Celsius"""
        celsius_data = (raw_data.astype(float) * self.thermal_resolution) - self.kelvin_offset
        return celsius_data
    
    def calculate_thermal_statistics(self, pixel_data: np.ndarray) -> Tuple[float, float, float, float, float]:
        """Calculate thermal statistics from raw pixel data, excluding negative values"""
        if pixel_data is None or pixel_data.size == 0:
            return None, None, None, None, None
        
        # Flatten array and filter out negative values (faulty pixels)
        flat_pixels = pixel_data.flatten()
        valid_pixels = flat_pixels[flat_pixels >= 0]
        
        if len(valid_pixels) == 0:
            logging.warning("⚠️ No valid thermal pixels after filtering negatives")
            return None, None, None, None, None
        
        try:
            min_temp = float(np.min(valid_pixels))
            max_temp = float(np.max(valid_pixels))
            avg_temp = float(np.mean(valid_pixels))
            median_temp = float(np.median(valid_pixels))
            
            # Calculate mode (most frequent temperature, rounded to 0.1°C)
            rounded_pixels = np.round(valid_pixels * 10) / 10
            unique_temps, counts = np.unique(rounded_pixels, return_counts=True)
            modal_temp = float(unique_temps[np.argmax(counts)])
            
            filtered_count = len(flat_pixels) - len(valid_pixels)
            if filtered_count > 0:
                logging.info(f"🔧 Filtered {filtered_count} negative pixels from {len(flat_pixels)} total pixels")
            
            return min_temp, max_temp, avg_temp, modal_temp, median_temp
            
        except Exception as e:
            logging.error(f"❌ Error calculating thermal statistics: {e}")
            return None, None, None, None, None
    
    def fetch_thermal_data(self) -> bool:
        """Fetch thermal camera data from tCam-Mini"""
        try:
            # Get thermal image
            data = self.connect_tcam_and_send({"cmd": "get_image"})
            if not data or 'radiometric' not in data:
                logging.warning("⚠️ No radiometric data received from tCam")
                self.sensor_data["thermal_camera"]["connection_status"] = "disconnected"
                return False
            
            # Decode thermal image
            img_data = base64.b64decode(data['radiometric'])
            thermal_array = np.frombuffer(img_data, dtype=np.uint16)
            thermal_raw = thermal_array.reshape((120, 160))
            
            # Convert raw data to temperature in Celsius
            thermal_celsius = self.raw_to_celsius(thermal_raw)
            
            # Calculate statistics
            min_temp, max_temp, avg_temp, modal_temp, median_temp = self.calculate_thermal_statistics(thermal_celsius)
            
            # Update sensor data
            self.sensor_data["thermal_camera"] = {
                "min_temp": min_temp,
                "max_temp": max_temp,
                "avg_temp": avg_temp,
                "modal_temp": modal_temp,
                "median_temp": median_temp,
                "last_update": datetime.now().isoformat(),
                "connection_status": "connected",
                "raw_image": thermal_celsius,
                "stats": {
                    "total_pixels": thermal_celsius.size,
                    "valid_pixels": len(thermal_celsius[thermal_celsius >= 0].flatten()),
                    "negative_pixels_filtered": len(thermal_celsius[thermal_celsius < 0].flatten())
                }
            }
            
            logging.info(f"✅ Thermal camera data updated - Temp range: {min_temp:.1f}°C to {max_temp:.1f}°C")
            return True
            
        except Exception as e:
            logging.error(f"❌ Thermal camera error: {e}")
            self.sensor_data["thermal_camera"]["connection_status"] = "disconnected"
            self.sensor_data["thermal_camera"]["last_update"] = datetime.now().isoformat()
            return False
    
    def get_sensor_data(self) -> Dict:
        """Get current sensor data"""
        return self.sensor_data.copy()
    
    def update_all_sensors(self) -> Dict[str, bool]:
        """Update all sensor data and return status"""
        results = {
            "feather_s3d": self.fetch_feather_s3d_data(),
            "thermal_camera": self.fetch_thermal_data()
        }
        
        logging.info(f"📊 Sensor update complete - Feather: {'✅' if results['feather_s3d'] else '❌'}, Thermal: {'✅' if results['thermal_camera'] else '❌'}")
        return results
