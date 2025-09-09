# Current Deployment Status - Jetson Greenhouse System

## System Architecture Overview

The greenhouse monitoring system is deployed with a modern nginx reverse proxy architecture serving both the Streamlit dashboard and Jetson API on a unified port.

### Port Configuration
- **Port 8082**: Nginx reverse proxy (unified access point)
- **Port 8083**: Jetson greenhouse server (internal API)
- **Port 8501**: Streamlit dashboard (internal)

### Access Points
- **Main Dashboard**: http://192.168.1.75:8082/
- **API Endpoints**: http://192.168.1.75:8082/api/*
- **Thermal Images**: http://192.168.1.75:8082/thermal_image.png

## Current System Status ✅

### Services Running
- ✅ `jetson-greenhouse.service` - Main sensor server (Port 8083)
- ✅ `jetson-streamlit.service` - Dashboard interface (Port 8501) 
- ✅ `jetson-nginx.service` - Reverse proxy (Port 8082)

### Hardware Connectivity
- ✅ **Feather S3[D]**: Connected at 192.168.1.81:8080
  - SHT45: Temperature & Humidity sensor
  - HDC3022: Temperature & Humidity sensor
- ✅ **tCam-Mini**: Connected at 192.168.1.130:5001
  - Thermal imaging with foliage temperature analysis

### Data Flow
```
Sensors → Jetson Server (8083) → Nginx Proxy (8082) → Dashboard/API
```

## Features Implemented

### Dashboard Features
- ✅ Streamlit-based modern web interface
- ✅ Simplified UI with removed Time Range dropdown and Auto-refresh checkbox
- ✅ Always-visible "Last Updated" timestamp display
- ✅ Fixed 5-second automatic refresh interval
- ✅ Manual "Refresh Now" button in sidebar
- ✅ Enhanced Time Series Plots with granular time ranges (15min, 30min, 2hr)
- ✅ Interactive Plotly charts with hover tooltips
- ✅ Dark/light theme support
- ✅ Connection status indicators
- ✅ Temperature, Humidity, and VPD monitoring

### API Features
- ✅ `/api/sensors` - Complete sensor data with status
- ✅ `/api/thermal_pixel_data` - Raw thermal camera data
- ✅ Real-time sensor readings from hardware
- ✅ VPD calculations (Air VPD, Enhanced VPD)
- ✅ Thermal image processing and serving

### Data Management
- ✅ CSV data logging with 7-day retention
- ✅ Data directory: `/home/lionel/jetson-greenhouse/data`
- ✅ Log file: `/home/lionel/jetson-greenhouse/jetson-greenhouse.log`
- ✅ Automatic data rotation and cleanup

## Recent Issues Resolved

### Sensor Connectivity ✅ FIXED
- **Issue**: Feather S3[D] and thermal camera showing "disconnected"
- **Cause**: Network connectivity failure to sensor devices
- **Resolution**: Power cycled both devices - now showing "connected"
- **Result**: Live sensor data flowing, plots showing varying values

### Path Configuration ✅ FIXED  
- **Issue**: Streamlit dashboard had hardcoded `/home/lio` paths
- **Resolution**: Updated to correct `/home/lionel` paths for Jetson user
- **Result**: Dashboard starts without permission errors

### Port Configuration ✅ FIXED
- **Issue**: Port conflicts between services
- **Resolution**: Implemented nginx reverse proxy architecture
- **Result**: Unified access on port 8082 with proper routing

## Deployment Scripts

### Primary Deployment
- `deploy_nginx_proxy.sh` - Complete system with reverse proxy
- `deploy_complete_jetson.sh` - Jetson server + Streamlit (no proxy)

### Configuration Files
- `nginx-greenhouse.conf` - Nginx reverse proxy configuration
- `jetson-greenhouse.service` - Main server systemd service
- `jetson-streamlit.service` - Dashboard systemd service
- `config/jetson_config.py` - System configuration

## Monitoring Commands

### Service Status
```bash
sudo systemctl status jetson-greenhouse.service
sudo systemctl status jetson-streamlit.service  
sudo systemctl status jetson-nginx.service
```

### Live Logs
```bash
sudo journalctl -u jetson-greenhouse.service -f
sudo journalctl -u jetson-streamlit.service -f
```

### API Testing
```bash
curl http://192.168.1.75:8082/api/sensors
ping 192.168.1.81  # Test Feather S3[D]
ping 192.168.1.130 # Test tCam-Mini
```

## System Health

### Current Sensor Readings (Last Check)
- **SHT45**: 27.7°C, 60.0% humidity
- **HDC3022**: 28.0°C, 63.4% humidity  
- **Thermal Range**: 24.2°C - 28.8°C
- **VPD**: ~1.4 kPa (optimal range)

### Performance
- **Response Time**: <50ms for API calls
- **Memory Usage**: ~140MB for main server
- **CPU Usage**: Low (<10% typical)
- **Data Storage**: ~876KB CSV data file

## Next Steps / Maintenance

1. **Monitor sensor connectivity** - Power cycle devices if "disconnected"
2. **Check disk space** - Data directory grows with continuous logging
3. **Update documentation** - Keep deployment guides current
4. **Backup configuration** - Preserve service files and configs

---
*Last Updated: 2025-08-26 12:34 GMT*
*System Status: ✅ FULLY OPERATIONAL*
