# Jetson Orin Nano Greenhouse Monitoring System

## Overview
Independent greenhouse monitoring system that operates concurrently with the BeaglePlay, providing redundancy and enhanced processing capabilities using the Jetson Orin Nano's superior computational power.

## System Architecture

### Hardware Components
- **Jetson Orin Nano**: Main processing unit (192.168.1.75:8082)
- **Feather S3[D]**: Dual precision sensors (SHT45 + HDC3022) at 192.168.1.81
- **tCam-Mini**: Thermal camera at 192.168.1.130
- **Network**: All devices on WiFi network BT-X6F962

### Key Features
- **Independent Operation**: No dependency on BeaglePlay
- **Concurrent Deployment**: Runs alongside BeaglePlay without interference
- **Enhanced Processing**: Leverages Jetson's GPU for future OpenCV/ML features
- **Redundancy**: Backup system if BeaglePlay fails
- **Modular Design**: Pluggable thermal processing strategies

## Installation

### Prerequisites
- Jetson Orin Nano with Ubuntu 20.04+
- Python 3.8+
- Network connectivity to sensors
- WiFi credentials for BT-X6F962

### Quick Install
```bash
# Clone repository (if not already done)
git clone https://github.com/PotentSoftware/greenhouse-monitoring.git
cd greenhouse-monitoring/jetson-orin-integration

# Run installation script
sudo ./install.sh
```

### Manual Installation
```bash
# Create installation directory
sudo mkdir -p /home/lionel/jetson-greenhouse
sudo chown lionel:lionel /home/lionel/jetson-greenhouse

# Copy files
cp -r src/ config/ requirements.txt /home/lionel/jetson-greenhouse/

# Create virtual environment
cd /home/lionel/jetson-greenhouse
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create data directory
mkdir -p /home/lionel/greenhouse-data
```

## Usage

### Service Management
```bash
# Start service
sudo systemctl start jetson-greenhouse

# Stop service
sudo systemctl stop jetson-greenhouse

# Restart service
sudo systemctl restart jetson-greenhouse

# Enable auto-start on boot
sudo systemctl enable jetson-greenhouse
```

### Management Scripts
```bash
# Check system status
/home/lionel/jetson-greenhouse/status.sh

# View logs
/home/lionel/jetson-greenhouse/logs.sh

# Follow logs in real-time
/home/lionel/jetson-greenhouse/logs.sh -f

# Test sensor connectivity
/home/lionel/jetson-greenhouse/test_connectivity.sh
```

### Manual Operation
```bash
cd /home/lionel/jetson-greenhouse
source venv/bin/activate
python src/jetson_greenhouse_server.py
```

## Access Points

### Web Interfaces
- **Jetson Dashboard**: http://192.168.1.75:8082/
- **Interactive Thermal Viewer**: http://192.168.1.75:8082/thermal_viewer
- **BeaglePlay Dashboard**: http://192.168.1.203:8080/ (concurrent)
- **JSON API**: http://192.168.1.75:8082/api/sensors

### API Endpoints
- `GET /` - Main dashboard
- `GET /api/sensors` - Complete sensor data (JSON)
- `GET /api/health` - System health check
- `GET /download/csv` - Download logged data
- `GET /thermal_viewer` - Interactive thermal image viewer
- `GET /thermal_image.png` - Real-time thermal image
- `GET /thermal_data.npy` - Thermal data in numpy format
- `GET /api/thermal_pixel_data` - Thermal pixel data for interactions
- `GET /api/get_available_collections` - List thermal image collections
- `GET /api/analysis_results` - Get thermal analysis results
- `POST /api/set_processing_strategy` - Change thermal processing method
- `POST /api/collect_thermal_images` - Start thermal image collection
- `POST /api/thermal_collection_status` - Get collection status
- `POST /api/analyze_thermal_collection` - Analyze thermal image collection

## Configuration

### Network Settings
Edit `/home/lionel/jetson-greenhouse/config/jetson_config.py`:
```python
JETSON_IP = "192.168.1.75"
JETSON_PORT = 8082
FEATHER_S3D_IPS = ['192.168.1.81']
TCAM_HOST = "192.168.1.130"
```

### Data Collection
```python
SENSOR_READ_INTERVAL = 5  # seconds
LOG_INTERVAL = 300  # 5 minutes
DATA_DIR = "/home/lionel/greenhouse-data"
```

## Features

### Sensor Integration
- **Feather S3[D]**: HTTP API communication for dual precision sensors
- **tCam-Mini**: Socket API communication for thermal imaging
- **Real-time Updates**: 5-second sensor reading intervals
- **Fallback Mechanisms**: USB serial backup for Feather S3[D]

### VPD Calculations
- **Air VPD**: Using averaged sensor temperature + humidity
- **Canopy VPD**: Using thermal temperature + air humidity  
- **Enhanced VPD**: Average of Air + Canopy VPD
- **Thermal VPD**: Pure thermal-based calculation
- **Individual Combinations**: 9 different VPD calculations with thermal data

### Thermal Processing
- **Basic Statistical**: Min, max, mean, median, mode analysis
- **OpenCV Simple**: Threshold-based region detection
- **Pluggable Architecture**: Easy to add new processing strategies
- **Negative Pixel Filtering**: Automatic faulty pixel exclusion
- **Advanced Segmentation**: CUDA-accelerated thermal segmentation and analysis

### Interactive Thermal Viewer
- **Real-time Thermal Imaging**: Live thermal camera feed with auto-refresh
- **Mouse Pixel Temperature**: Hover over any pixel to see its temperature
- **Click-to-Record**: Click pixels to record coordinates and temperature
- **Persistent Tracking**: Recorded pixels update temperature on each refresh
- **Temperature History**: View original and current temperatures for recorded pixels
- **Smooth Refresh**: Flicker-free image updates using preloading
- **Professional UI**: Dark theme with temperature colorbar and statistics

### Thermal Image Collection & Analysis
- **Automated Collection**: Collect multiple thermal images at specified intervals
- **Collection Management**: View and select from available thermal image collections
- **Statistical Analysis**: Comprehensive temperature statistics with PCA analysis
- **Interactive Visualizations**: Temperature distributions, histograms, and correlation plots
- **Persistent Results**: Analysis results preserved until manually cleared
- **Smart Auto-refresh**: Pauses during analysis and when results are available

### Data Logging
- **CSV Format**: Complete sensor data every 5 minutes
- **JSON Format**: Latest reading in structured format
- **Data Retention**: Automatic cleanup after 90 days
- **Export Function**: Download historical data via web interface

## Concurrent Operation

### Port Configuration
- **Jetson**: Port 8082 (this system)
- **BeaglePlay**: Port 8080 (existing system)
- **No Conflicts**: Systems operate independently

### Data Comparison
Both systems read from the same sensors but process independently:
- Compare data consistency between systems
- Validate thermal processing algorithms
- Ensure redundancy in case of system failure

### Network Architecture
```
WiFi Network (BT-X6F962)
├── Jetson Orin Nano (192.168.1.75:8082)
├── BeaglePlay (192.168.1.203:8080)
├── Feather S3[D] (192.168.1.81:8080)
└── tCam-Mini (192.168.1.130:5001)
```

## Future Enhancements

### OpenCV Integration
The system is designed with a pluggable architecture for advanced image processing:

```python
# Add new processing strategy
from thermal_processor import ThermalProcessorStrategy

class MLSegmentationProcessor(ThermalProcessorStrategy):
    def process_image(self, thermal_image):
        # Implement ML-based leaf segmentation
        pass
    
    def get_canopy_temperature(self, thermal_image):
        # Extract temperature from segmented regions
        pass

# Register new strategy
thermal_processor.add_strategy('ml_segmentation', MLSegmentationProcessor())
thermal_processor.set_processing_strategy('ml_segmentation')
```

### Machine Learning
- Leaf detection and segmentation
- Plant health assessment
- Predictive analytics
- Automated irrigation control

### Advanced Analytics
- Historical trend analysis
- Anomaly detection
- Environmental optimization
- Growth pattern recognition

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
sudo journalctl -u jetson-greenhouse -f

# Test connectivity
/home/lionel/jetson-greenhouse/test_connectivity.sh

# Check permissions
sudo chown -R lionel:lionel /home/lionel/jetson-greenhouse
```

**Sensor connectivity issues:**
```bash
# Test Feather S3[D]
curl http://192.168.1.81:8080/sensors

# Test tCam-Mini
nc -z 192.168.1.130 5001
```

**Port conflicts:**
```bash
# Check what's using port 8082
sudo netstat -tulpn | grep :8082

# Kill conflicting processes
sudo fuser -k 8082/tcp
```

### Log Files
- **Service Logs**: `sudo journalctl -u jetson-greenhouse`
- **Application Log**: `/home/lionel/jetson-greenhouse.log`
- **Data Logs**: `/home/lionel/greenhouse-data/`

## Development

### Project Structure
```
jetson-orin-integration/
├── src/
│   ├── jetson_greenhouse_server.py    # Main server with thermal analysis
│   ├── sensor_manager.py              # Sensor communication
│   ├── thermal_processor.py           # Image processing
│   ├── thermal_image_analyzer.py      # Statistical analysis & PCA
│   ├── thermal_image_collector.py     # Automated image collection
│   └── vpd_calculator.py              # VPD calculations
├── config/
│   └── jetson_config.py               # Configuration
├── templates/                         # HTML templates (if any)
├── requirements.txt                   # Dependencies
├── install.sh                         # Installation script
└── README.md                          # This file
```

### Adding New Features
1. **New Sensor**: Extend `SensorManager` class
2. **New VPD Type**: Add method to `VPDCalculator`
3. **New Processing**: Implement `ThermalProcessorStrategy`
4. **New Endpoint**: Add route to `JetsonHTTPHandler`

### Testing
```bash
# Test individual components
cd /home/lionel/jetson-greenhouse
source venv/bin/activate

# Test sensor manager
python -c "from src.sensor_manager import SensorManager; import config.jetson_config as config; sm = SensorManager(config); print(sm.update_all_sensors())"

# Test VPD calculator
python -c "from src.vpd_calculator import VPDCalculator; vc = VPDCalculator(); print(vc.calculate_vpd(25, 60))"
```

## Support

### System Requirements
- **OS**: Ubuntu 20.04+ (Jetson)
- **Python**: 3.8+
- **Memory**: 4GB+ RAM
- **Storage**: 32GB+ (for data logging)
- **Network**: WiFi connectivity to sensors

### Dependencies
- Flask (web framework)
- NumPy/SciPy (numerical computing)
- OpenCV (image processing)
- Matplotlib (visualization)
- Requests (HTTP communication)

### Contact
- **Project**: Greenhouse Monitoring System
- **Platform**: Jetson Orin Nano
- **Concurrent Operation**: With BeaglePlay system
- **Repository**: https://github.com/PotentSoftware/greenhouse-monitoring
