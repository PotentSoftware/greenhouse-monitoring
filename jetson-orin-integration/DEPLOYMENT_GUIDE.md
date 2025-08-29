# Jetson Orin Nano Greenhouse Monitoring - Deployment Guide

## Overview
This system provides real-time greenhouse monitoring with thermal foliage segmentation, enhanced VPD calculations, and dynamic time series plotting with independent y-axis scaling controls.

## Prerequisites

### Hardware Requirements
- NVIDIA Jetson Orin Nano
- Feather S3[D] sensor board (192.168.1.81)
- tCam-Mini thermal camera (192.168.1.130)
- Network connectivity for all devices

### Software Requirements
- Python 3.8+
- CUDA 12.x support
- Required Python packages (see requirements.txt)

## Installation Steps

### 1. Clone Repository
```bash
cd /home/lionel
git clone https://github.com/your-repo/greenhouse-monitoring.git
cd greenhouse-monitoring/jetson-orin-integration
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Data Directory
```bash
mkdir -p /home/lionel/greenhouse-data
chmod 755 /home/lionel/greenhouse-data
```

### 5. Configure Network Settings
Edit `src/jetson_greenhouse_server.py` if needed to update device IPs:
- Feather S3[D]: `192.168.1.81`
- tCam-Mini: `192.168.1.130`
- Jetson server: `192.168.1.75:8082`

## Running the System

### Manual Start
```bash
cd /home/lionel/greenhouse-monitoring/jetson-orin-integration
source venv/bin/activate
python src/jetson_greenhouse_server.py
```

### Systemd Service (Recommended)
Create service file:
```bash
sudo nano /etc/systemd/system/jetson-greenhouse.service
```

Service configuration:
```ini
[Unit]
Description=Jetson Greenhouse Monitoring System
After=network.target

[Service]
Type=simple
User=lionel
WorkingDirectory=/home/lionel/greenhouse-monitoring/jetson-orin-integration
Environment=PATH=/home/lionel/greenhouse-monitoring/jetson-orin-integration/venv/bin
ExecStart=/home/lionel/greenhouse-monitoring/jetson-orin-integration/venv/bin/python src/jetson_greenhouse_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jetson-greenhouse.service
sudo systemctl start jetson-greenhouse.service
```

## System Features

### Dashboard Access
- **Main Dashboard**: http://192.168.1.75:8082/
- **Time Series Plots**: http://192.168.1.75:8082/plots
- **Data Download**: http://192.168.1.75:8082/download/csv

### Key Features
1. **Real-time Monitoring**: Live sensor data from Feather S3[D]
2. **Thermal Integration**: CUDA-accelerated foliage segmentation from tCam-Mini
3. **Enhanced VPD**: Multiple VPD calculations using foliage temperature
4. **Dynamic Plotting**: Independent y-axis scaling for each plot type
5. **Data Logging**: Automatic CSV/JSON logging with 5-second intervals
6. **Auto-refresh**: 5-second plot updates with user-selected scaling

### Plot Controls
- **Temperature Y-Axis**: Independent scaling for temperature trends
- **Humidity Y-Axis**: Independent scaling for humidity trends  
- **VPD Y-Axis**: Independent scaling for VPD analysis
- **Foliage Y-Axis**: Independent scaling for thermal foliage data

Scaling options: Data Range + Margin, Auto Scale, Tight Fit, Fixed Range

## Monitoring and Logs

### Check Service Status
```bash
sudo systemctl status jetson-greenhouse.service
```

### View Logs
```bash
sudo journalctl -u jetson-greenhouse.service -f
```

### Data Files
- **CSV Data**: `/home/lionel/greenhouse-data/jetson_sensor_data.csv`
- **JSON Data**: `/home/lionel/greenhouse-data/latest_sensor_data.json`

## Troubleshooting

### Common Issues
1. **Port 8082 in use**: Kill existing processes or change port
2. **CUDA errors**: Ensure CUDA 12.x is properly installed
3. **Sensor connectivity**: Verify network connectivity to devices
4. **Permission errors**: Ensure lionel user has write access to data directory

### Network Connectivity Test
```bash
# Test Feather S3[D]
curl http://192.168.1.81/sensor-data

# Test tCam-Mini
curl http://192.168.1.130:8080/status
```

### Reset Data
```bash
rm /home/lionel/greenhouse-data/jetson_sensor_data.csv
rm /home/lionel/greenhouse-data/latest_sensor_data.json
```

## Performance Optimization

### CUDA Memory Management
The system uses CuPy for GPU-accelerated thermal processing. Monitor GPU memory:
```bash
nvidia-smi
```

### Data Retention
CSV data is automatically managed with configurable retention periods in the server code.

## Security Considerations

- System runs on local network (192.168.1.x)
- No external internet access required for core functionality
- Data stored locally on Jetson storage
- Consider firewall rules if exposing beyond local network

## Updates and Maintenance

### Update Code
```bash
cd /home/lionel/greenhouse-monitoring
git pull origin main
sudo systemctl restart jetson-greenhouse.service
```

### Backup Data
```bash
cp /home/lionel/greenhouse-data/*.csv /backup/location/
```

## Support

For issues or questions:
1. Check system logs with `journalctl`
2. Verify network connectivity to sensors
3. Monitor GPU memory usage with `nvidia-smi`
4. Review data file permissions and disk space
