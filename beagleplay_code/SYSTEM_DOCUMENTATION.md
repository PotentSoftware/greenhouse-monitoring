# 🌱 Greenhouse Monitoring System - Complete Documentation

## 📡 **System URLs & Endpoints**

### **Primary Dashboard**
- **Main Dashboard**: `http://192.168.1.203:8082/`
  - Dark mode interface with landscape layout
  - Real-time BeagleConnect Freedom sensor data
  - Thermal camera statistics
  - Auto-refreshing timestamps

### **Alternative Access Points**
- **Node-RED Dashboard**: `http://192.168.1.203:1880/ui`
  - Alternative web interface
  - Node-RED flow-based dashboard

## 🎯 **Data Sources & Endpoints**

### **BeagleConnect Freedom Sensors**
**Physical Location**: Connected to BeaglePlay via IIO (Industrial I/O) subsystem
**Data Access Method**: Direct file system reads from `/sys/bus/iio/devices/`

**Sensor Mappings**:
- **Temperature**: `/sys/bus/iio/devices/iio:deviceX/in_temp_input`
- **Humidity**: `/sys/bus/iio/devices/iio:deviceX/in_humidityrelative_input`  
- **pH Sensor**: `/sys/bus/iio/devices/iio:deviceX/in_ph_input` or `/sys/bus/iio/devices/iio:deviceX/in_voltage_input`

**Data Format**: Raw sensor values read from IIO device files
**Update Frequency**: Continuous polling every 2 seconds
**Units**: 
- Temperature: °C
- Humidity: %RH
- pH: pH units (0-14 scale)

### **Thermal Camera (ESP32-S3)**
**Primary URL**: `http://192.168.1.176/thermal_data`
**Fallback URLs**: `http://192.168.1.100/thermal_data`, `http://192.168.1.101/thermal_data`, `http://192.168.1.102/thermal_data`
**Visual Interface**: `http://192.168.1.176/` (Shows heatmap and histogram)

**Expected JSON Response Format**:
```json
{
  "min_temp": 18.5,
  "max_temp": 28.3,
  "mean_temp": 23.1,
  "median_temp": 22.8,
  "range_temp": 9.8,
  "mode_temp": 23.0,
  "std_dev_temp": 2.4
}
```

**Data Statistics Provided**:
- **Min Temperature**: Lowest temperature in thermal image
- **Max Temperature**: Highest temperature in thermal image  
- **Mean Temperature**: Average temperature across all pixels
- **Median Temperature**: Middle value when all temperatures sorted
- **Range Temperature**: Difference between max and min
- **Mode Temperature**: Most frequently occurring temperature
- **Standard Deviation**: Temperature variation measure

**Update Frequency**: Every 10 seconds
**Connection Timeout**: 2 seconds
**Units**: °C (Celsius)

## 🔧 **System Architecture**

### **BeaglePlay Device** (`192.168.1.203`)
- **OS**: Debian GNU/Linux 11 (Bullseye)
- **Python Server**: `ph_web_server_alt_port.py` on port 8082
- **Service Name**: `integrated-greenhouse.service` (systemd)
- **Working Directory**: `/home/debian/`
- **User**: `debian`

### **Port Configuration**
- **8080**: Reserved (original server - may conflict)
- **8081**: Reserved (first alternative)
- **8082**: **Active Server Port** ✅
- **1880**: Node-RED service

## 📊 **Data Processing & Display**

### **VPD (Vapor Pressure Deficit) Calculation**
```python
# Saturated Vapor Pressure (kPa)
svp = 0.6108 * math.exp(17.27 * temp_value / (temp_value + 237.3))

# Actual Vapor Pressure (kPa)  
avp = svp * (humidity_value / 100)

# VPD (kPa)
vpd = svp - avp
```

### **Connection Status Logic**
- **BeagleConnect**: Status based on successful IIO device detection
- **Thermal Camera**: 
  - **Connected**: Successfully receiving data from `192.168.1.176`
  - **Simulated**: Fallback mode with realistic test data

## 🚀 **Deployment & Operations**

### **Manual Startup**
```bash
ssh debian@192.168.1.203
cd /home/debian
python3 ph_web_server_alt_port.py
```

### **Systemd Service Setup**
```bash
# Enable auto-start on boot
sudo systemctl enable integrated-greenhouse.service
sudo systemctl start integrated-greenhouse.service

# Check status
sudo systemctl status integrated-greenhouse.service
```

### **Troubleshooting Commands**
```bash
# Check port usage
sudo netstat -tulpn | grep :8082

# Check service logs
sudo journalctl -u integrated-greenhouse.service -f

# Kill hanging processes
sudo pkill -f python3
```

## 🔍 **Monitoring & Debugging**

### **Log Files**
- **System Logs**: `/var/log/syslog`
- **Service Logs**: `sudo journalctl -u integrated-greenhouse.service`
- **Application Logs**: Console output when running manually

### **Health Checks**
- **Dashboard Access**: `http://192.168.1.203:8082/`
- **BeagleConnect Status**: Check sensor values are non-zero and updating
- **Thermal Camera Status**: Verify "Connected" status in dashboard
- **Data Updates**: Timestamps should refresh every 10 seconds

## 📋 **Feature Summary**

### **Dashboard Features**
- ✅ **Dark Mode**: Full dark theme interface
- ✅ **Landscape Layout**: Optimized for wide screens
- ✅ **Real-time Timestamps**: Updates every 10 seconds
- ✅ **Responsive Design**: Adapts to different screen sizes
- ✅ **Auto-refresh**: No manual refresh needed
- ✅ **Error Handling**: Graceful fallbacks for disconnected sensors

### **Data Integration**
- ✅ **BeagleConnect Freedom**: pH, Temperature, Humidity, VPD
- ✅ **Thermal Camera**: 7 statistical measurements
- ✅ **Combined Display**: Single unified interface
- ✅ **Independent Operation**: Runs without laptop dependency

### **System Reliability**
- ✅ **Auto-restart**: systemd service configuration
- ✅ **Port Conflict Resolution**: Multiple port options
- ✅ **Connection Fallbacks**: Simulated data when hardware unavailable
- ✅ **Error Logging**: Comprehensive debugging information

---

**Last Updated**: 2025-06-16  
**System Version**: Port 8082 (Stable)  
**Thermal Camera**: `192.168.1.176` (Primary)
