#!/usr/bin/env python3
"""
Jetson Orin Nano Configuration
Independent greenhouse monitoring system configuration
"""

# Network Configuration
JETSON_IP = "0.0.0.0"  # Bind to all interfaces for network access
JETSON_PORT = 8082

# Sensor Configuration
FEATHER_S3D_IPS = ['192.168.1.81']
FEATHER_S3D_PORT = 8080
FEATHER_S3D_TIMEOUT = 5

# Thermal Camera Configuration
TCAM_HOST = "192.168.1.130"
TCAM_PORT = 5001
TCAM_TIMEOUT = 5

# Data Collection Settings
SENSOR_READ_INTERVAL = 5  # seconds
LOG_INTERVAL = 5  # 5 seconds for time series plotting
DATA_RETENTION_DAYS = 90

# Data Storage Paths
DATA_DIR = "/home/lionel/jetson-greenhouse/data"
CSV_FILE = "jetson_sensor_data.csv"
JSON_FILE = "jetson_latest_data.json"

# Thermal Processing Settings
THERMAL_RESOLUTION = 0.01  # Kelvin per raw unit for Lepton 3.5
KELVIN_OFFSET = 273.15

# Image Processing Settings (for future OpenCV integration)
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 120
PROCESSING_STRATEGIES = {
    'basic': 'BasicThermalProcessor',
    'opencv_simple': 'OpenCVSimpleProcessor',
    'opencv_advanced': 'OpenCVAdvancedProcessor',
    'ml_segmentation': 'MLSegmentationProcessor'
}

# Web Interface Settings
DASHBOARD_TITLE = "Jetson Orin Nano Greenhouse Monitor"
AUTO_REFRESH_INTERVAL = 10  # seconds
THEME = "dark"

# System Settings
LOG_LEVEL = "INFO"
LOG_FILE = "/home/lionel/jetson-greenhouse/jetson-greenhouse.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Concurrent Operation Settings
BEAGLEPLAY_URL = "http://192.168.1.203:8080"
ENABLE_COMPARISON = True
COMPARISON_TOLERANCE = {
    'temperature': 2.0,  # degrees C
    'humidity': 5.0,     # percent
    'vpd': 0.2          # kPa
}
