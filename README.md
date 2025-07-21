# 🌱 Greenhouse IoT Monitoring System

A professional 24/7 greenhouse monitoring system integrating BeaglePlay pH/humidity sensors with ESP32-S3 thermal imaging for enhanced plant health management.

## 🏗️ System Architecture

```
BeagleConnect Freedom → BeaglePlay → Python Web Server (Port 8080)
    (pH, RH, T_air)       ↓              ↓
                    IIO Sensors    Integrated Dashboard
                                         ↑
ESP32-S3 Thermal Camera ─────────────────┘
(T_canopy, real-time updates)                                  
```

### Firmware Components
- **BeagleConnect Freedom**: Custom Zephyr firmware with Greybus protocol
- **ESP32-S3 Thermal Camera**: Standalone thermal imaging with web interface
- **BeaglePlay**: Linux host running Python web server and Greybus gateway

**Key Features:**
- **Integrated Dashboard** with dark mode and landscape layout
- **Real-time Sensor Data** from BeagleConnect Freedom
- **Thermal Camera Integration** with fallback simulation
- **24/7 Independent Operation** with systemd service
- **VPD Calculation** using air temperature, humidity, and actual canopy temperature
- **Automatic Startup** after power cycles

## 🚀 Quick Start

### Access Your Dashboards
- **🌡️ Main Dashboard**: http://192.168.1.203:8080/ (Integrated sensor + thermal data)
- **📷 Thermal Camera**: http://192.168.1.176/ (Direct camera interface)
- **🔧 Node-RED Editor**: http://192.168.1.203:1880/ (Optional flow configuration)

### System Status
The system runs independently on the BeaglePlay device with:
- Python web server on port 8080
- Automatic service startup via systemd
- Thermal camera fallback for reliability
- Real-time sensor data updates

## 📊 Dashboard Features

### Integrated Python Dashboard (Port 8080)
- **Dark Mode Interface** optimized for greenhouse environments
- **Landscape Layout** for tablet/monitor viewing
- **Real-time Timestamps** showing last data update
- **BeagleConnect Freedom Data**: pH, Temperature, Humidity, VPD
- **Thermal Camera Statistics**: Min, Max, Mean, Median, Range, Mode, Std Dev
- **Connection Status**: Shows if thermal camera is connected or simulated
- **Auto-refresh**: Updates every few seconds

### BeagleConnect Freedom Sensors
- **pH Sensor**: Soil/water pH monitoring
- **Temperature Sensor**: Air temperature (°C)
- **Humidity Sensor**: Relative humidity (%)
- **VPD Calculation**: Vapor Pressure Deficit (kPa)

### ESP32-S3 Thermal Camera
- **Temperature Statistics**: Comprehensive thermal analysis
- **Fallback Mode**: Continues with simulated data if camera disconnected
- **Multiple IP Support**: Tries multiple camera addresses for reliability

## 🔧 Hardware Configuration

### ESP32-S3 Thermal Camera
- **Status**: Connected at http://192.168.1.176/
- **Update Rate**: Real-time updates
- **Resolution**: 32x24 thermal array  
- **Data Endpoint**: `/thermal_data` (JSON API)
- **Fallback**: Automatic simulation if disconnected

### BeaglePlay + BeagleConnect Freedom
- **pH Sensor**: Soil/water monitoring via IIO device
- **Temperature**: Air temperature sensor
- **Humidity**: Relative humidity sensor  
- **Connection**: I2C via IIO subsystem
- **Update Rate**: Continuous monitoring

## ⚙️ System Management

### BeaglePlay Service Control
The system runs as a systemd service for automatic startup and recovery:

```bash
# Check service status
sudo systemctl status greenhouse-webserver.service

# Start the service
sudo systemctl start greenhouse-webserver.service

# Stop the service  
sudo systemctl stop greenhouse-webserver.service

# Restart the service
sudo systemctl restart greenhouse-webserver.service

# View service logs
sudo journalctl -u greenhouse-webserver.service -f
```

### Service Features
- **Automatic Startup**: Starts automatically on boot
- **Auto-Recovery**: Restarts if the service crashes
- **Independent Operation**: Runs without laptop/USB connection
- **Logging**: All activity logged to system journal

## 🚀 Deployment Instructions

### On BeaglePlay Device:
1. **Copy files to BeaglePlay**:
   ```bash
   scp beagleplay_code/ph_web_server.py debian@192.168.1.203:/home/debian/beagleplay_code/
   scp beagleplay_code/greenhouse-webserver.service debian@192.168.1.203:/home/debian/beagleplay_code/
   ```

2. **Install and enable service**:
   ```bash
   ssh debian@192.168.1.203
   sudo cp /home/debian/beagleplay_code/greenhouse-webserver.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable greenhouse-webserver.service
   sudo systemctl start greenhouse-webserver.service
   ```

3. **Verify installation**:
   ```bash
   sudo systemctl status greenhouse-webserver.service
   curl http://localhost:8080/
   ```

## 📁 Project Structure

```
/home/lio/github/greenhouse-monitoring/
├── beagleplay_code/                    # 🖥️ BeaglePlay server code
│   ├── ph_web_server.py                # 🐍 Main Python web server (Port 8080)
│   ├── greenhouse-webserver.service    # 🔧 Systemd service file
│   ├── CLEANUP_NOTES.md               # 📝 System cleanup documentation
│   └── ph_web_server_alt_port.py.backup # 🗄️ Backup of old server
├── firmware/                           # 🔧 Firmware development
│   ├── beagleconnect-freedom/          # 📦 Git submodule: BeagleConnect firmware
│   └── tools/
│       └── build-and-flash.sh          # 🛠️ Firmware build and flash script
├── docs/
│   └── firmware/
│       └── beagleconnect-freedom-development.md # 📖 Firmware dev guide
├── infrastructure/                     # 🏗️ System configuration
├── node-red-flows/                     # 🔄 Node-RED flows (optional)
│   └── greenhouse_dark_mode_flow.json
├── FIRMWARE_INTEGRATION_PLAN.md        # 📋 Integration documentation
└── README.md                          # 📚 This documentation
```

## 🛠️ Troubleshooting

### Service Issues
```bash
# Check if service is running
sudo systemctl status greenhouse-webserver.service

# View service logs
sudo journalctl -u greenhouse-webserver.service -f

# Restart service
sudo systemctl restart greenhouse-webserver.service
```

### Thermal Camera Issues
- Check camera power and network connection
- Verify camera IP address: http://192.168.1.176/
- System automatically falls back to simulated data if camera is disconnected
- Dashboard shows "Simulated (Camera Disconnected)" when using fallback data

### Sensor Data Issues
- BeagleConnect Freedom sensors are accessed via Linux IIO subsystem
- Check IIO devices: `ls /sys/bus/iio/devices/`
- Service logs show sensor detection status

## 🔧 Firmware Development

### BeagleConnect Freedom Firmware
The BeagleConnect Freedom runs custom Zephyr firmware with Greybus protocol support for wireless sensor communication.

#### Quick Start
```bash
# Build and flash firmware (from project root)
./firmware/tools/build-and-flash.sh
```

#### Development Setup
```bash
# Initialize firmware submodule
git submodule update --init --recursive

# Set up Zephyr environment
python3 -m venv .venv
source .venv/bin/activate
pip install west

# Initialize west workspace
west init -l firmware/beagleconnect-freedom
west update
```

#### Custom Features
- **I2C Protocol**: OPT3001 light sensor, HDC2010 temp/humidity sensor
- **Greybus Integration**: Wireless communication with BeaglePlay
- **SVC Protocol**: Service enumeration and power management
- **Debug Logging**: Comprehensive debugging support

#### Documentation
- **Complete Guide**: [docs/firmware/beagleconnect-freedom-development.md](docs/firmware/beagleconnect-freedom-development.md)
- **Integration Plan**: [FIRMWARE_INTEGRATION_PLAN.md](FIRMWARE_INTEGRATION_PLAN.md)

### ESP32-S3 Thermal Camera
Standalone thermal imaging system with web interface and dark mode.

#### Features
- **Real-time Thermal Imaging**: 32x24 pixel thermal sensor
- **Web Interface**: http://192.168.1.176/ with dark theme
- **Statistics**: Min, max, mean, median, range, mode, std dev
- **Histogram**: 50-bin temperature distribution
- **API Integration**: JSON endpoint for greenhouse system

## 📈 System Performance

### Resource Usage
- **CPU**: <2% average load on BeaglePlay
- **Memory**: ~50MB for Python web server
- **Network**: Local traffic only, minimal bandwidth
- **Storage**: Lightweight logging, <10MB/day

### Update Rates
- **Thermal Data**: Real-time from ESP32-S3 camera
- **Sensor Data**: Continuous monitoring via IIO subsystem
- **Dashboard**: Auto-refresh every few seconds
- **Service**: Automatic restart on failure

## 🎯 System Status

**🟢 ACTIVE COMPONENTS:**
- **Main Dashboard**: http://192.168.1.203:8080/ ✅
- **Thermal Camera**: http://192.168.1.176/ ✅  
- **BeagleConnect Sensors**: pH, Temperature, Humidity ✅
- **Systemd Service**: Auto-startup enabled ✅
- **VPD Calculation**: Real-time computation ✅

**🟡 OPTIONAL COMPONENTS:**
- **Node-RED Editor**: http://192.168.1.203:1880/ (for customization)
- **Node-RED Dashboard**: http://192.168.1.203:1880/ui (redundant, can disable)

**✅ SYSTEM READY** - Greenhouse monitoring system is operational and running independently on BeaglePlay!

### VPD Calculation
**Standard VPD** using air temperature and relative humidity from BeagleConnect Freedom:
```
VPD = SVP(T_air) × (1 - RH/100)

Where:
- T_air: Air temperature from BeagleConnect sensor (°C)
- RH: Relative humidity from BeagleConnect sensor (%)
- SVP: Saturated Vapor Pressure
```

**Enhanced VPD** using actual canopy temperature from thermal camera:
```
Enhanced VPD = SVP(T_canopy) - AVP(T_air, RH)

Where:
- T_canopy: Real canopy temperature from thermal camera (Max, Mean, Median, Mode)
- T_air: Air temperature from BeagleConnect sensor (°C)  
- RH: Relative humidity from BeagleConnect sensor (%)
- SVP: Saturated Vapor Pressure at canopy temperature
- AVP: Actual Vapor Pressure = SVP(T_air) × (RH/100)
```

**Benefits:**
- **Standard VPD**: Basic plant stress assessment using air conditions
- **Enhanced VPD**: More accurate plant stress using actual leaf/canopy temperature
- **Multiple measurements**: Max, Mean, Median, Mode temperatures provide comprehensive analysis
- **Real-time monitoring**: Continuous updates for precise irrigation timing

Happy monitoring! 🌱📊