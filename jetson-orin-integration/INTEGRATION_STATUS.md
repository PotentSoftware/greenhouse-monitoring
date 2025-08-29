# Greenhouse Monitoring System Integration Status

## Overview
This document describes the current state of the greenhouse monitoring system running on Jetson Orin Nano with real sensor integration.

## System Components

### 1. ESP32-S3 Sensor Module ✅
- **Status**: Fully operational
- **IP Address**: 192.168.1.81
- **Port**: 8080
- **Sensors**: SHT45 and HDC3022 (temperature/humidity)
- **API Endpoint**: http://192.168.1.81:8080/sensors
- **Data Format**: JSON with temperature, humidity, and VPD calculations

### 2. tCam-Mini Thermal Camera ⚠️
- **Status**: Limited connectivity
- **IP Address**: 192.168.1.130
- **Issue**: HTTP server only runs in AP mode, not station mode
- **Previous Setup**: Was accessible via web interface at 192.168.1.223:8080 (development laptop)
- **Current Workaround**: 
  - Primary: tcam_web_interface.py running on Jetson (localhost:8080)
  - Fallback: Proxy server with simulated data (localhost:5002)

### 3. Streamlit Dashboard ✅
- **Status**: Running
- **Port**: 8501
- **Access**: http://192.168.1.75:8501
- **Features**:
  - Real-time sensor data from ESP32-S3
  - Simulated thermal camera data (via proxy)
  - Historical data collection
  - Data analysis tools

### 4. tCam Web Interface ✅
- **Status**: Running
- **Port**: 8080
- **Purpose**: Bridge between tCam-Mini and HTTP clients
- **Note**: Cannot connect when tCam-Mini port 5001 is closed
- **Endpoints**:
  - `/thermal_raw` - Raw thermal data
  - `/thermal_image` - Thermal image visualization
  - `/status` - Connection status
  - `/device_info` - Device information

### 5. tCam Proxy Server ✅
- **Status**: Running (fallback)
- **Port**: 5002
- **Purpose**: Provides simulated thermal data when tCam-Mini is inaccessible
- **Endpoints**:
  - `/thermal_data` - JSON thermal array
  - `/thermal_image` - PNG image
  - `/thermal_stats` - Temperature statistics
  - `/status` - Server status

## Quick Start

### Starting All Services
```bash
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration
./start_all_services.sh
```

### Accessing the Dashboard
Open a web browser and navigate to: http://192.168.1.75:8501

### Manual Service Control

#### Start tCam Web Interface
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts
python3 tcam_web_interface.py
```

#### Start tCam Proxy Server (Fallback)
```bash
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration/src
python3 tcam_proxy_server.py
```

#### Start Streamlit Dashboard
```bash
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration
source venv/bin/activate
streamlit run streamlit_dashboard.py --server.port=8501 --server.address=0.0.0.0
```

## Known Issues and Limitations

### tCam-Mini Connectivity
- The tCam-Mini thermal camera only runs its HTTP/socket server in Access Point (AP) mode
- In station mode (connected to home WiFi), port 5001 is closed
- Current workaround uses simulated thermal data through the proxy server

### Potential Solutions for tCam-Mini
1. **AP Mode Bridge** (implemented but not active):
   - Module: `tcam_ap_bridge.py`
   - Temporarily switches Jetson to tCam AP network
   - Fetches real thermal data
   - Returns to home network
   - Note: Causes brief network disconnection

2. **Firmware Modification**:
   - Modify tCam-Mini firmware to enable HTTP server in station mode
   - Requires ESP32 development environment

3. **Dedicated Network Interface**:
   - Use USB WiFi adapter on Jetson
   - Keep one interface on home network
   - Connect second interface to tCam AP

## Data Flow

```
ESP32-S3 Sensors (192.168.1.81:8080)
    ↓ [REST API]
    ↓
Streamlit Data Adapter
    ↓
Streamlit Dashboard (192.168.1.75:8501)
    ↑
    ↑ [REST API - Primary]
tCam Web Interface (localhost:8080)
    ↑ [Attempts connection]
    X [Blocked]
tCam-Mini (192.168.1.130:5001) - Port closed in station mode
    
    ↓ [Fallback]
tCam Proxy Server (localhost:5002)
    ↑ [Simulated Data]
```

## Monitoring System Health

### Check Service Status
```bash
# Check if services are running
ps aux | grep -E "streamlit|tcam_proxy"

# Check ESP32 sensor connectivity
curl http://192.168.1.81:8080/sensors

# Check tCam web interface
curl http://localhost:8080/status

# Check tCam proxy (fallback)
curl http://localhost:5002/status

# Check Streamlit
curl http://localhost:8501
```

### View Logs
```bash
# Streamlit logs
tail -f /tmp/streamlit.log

# tCam proxy logs
tail -f /tmp/tcam_proxy.log
```

## Next Steps

1. **Resolve tCam-Mini Connectivity**:
   - Test AP mode bridge implementation
   - Or modify firmware for station mode support
   - Or implement dual-network solution

2. **System Hardening**:
   - Create systemd services for automatic startup
   - Implement proper logging and monitoring
   - Add error recovery mechanisms

3. **Feature Enhancement**:
   - Add alerts for abnormal conditions
   - Implement data export functionality
   - Create mobile-friendly interface

## Troubleshooting

### Dashboard Not Loading
1. Check if Streamlit is running: `ps aux | grep streamlit`
2. Check logs: `tail -f /tmp/streamlit.log`
3. Restart services: `./start_all_services.sh`

### No Sensor Data
1. Verify ESP32 is powered and connected to WiFi
2. Check connectivity: `ping 192.168.1.81`
3. Test API: `curl http://192.168.1.81:8080/sensors`

### Thermal Data Shows "Simulated"
This is expected behavior until tCam-Mini connectivity is resolved.
The proxy server provides realistic simulated data as a placeholder.

## Contact
For issues or questions about this integration, refer to the project repository at:
https://github.com/PotentSoftware/greenhouse-monitoring
