# 🌱 Greenhouse Monitoring System - Solution Guide

## Issues Identified & Solutions

### 1. **BeagleConnect Data Showing All 0s** ❌ → ✅
**Problem**: Device key mapping mismatch in sensor detection
**Solution**: Fixed `find_iio_devices()` function to use correct key names and added better error logging

### 2. **Dark Mode Not Working** ❌ → ✅  
**Problem**: You're accessing Node-RED (port 1880) instead of Python server (port 8080)
**Solution**: Access the correct URL or implement dark mode in Node-RED

### 3. **No DateTime Stamp** ❌ → ✅
**Problem**: Timestamp only available in Python server, not Node-RED
**Solution**: Implemented in both solutions

### 4. **URL Stops Updating When Laptop Sleeps** ❌ → ✅
**Problem**: USB connection dependency
**Solution**: Set up systemd service for independent operation

## 🎯 **IMMEDIATE ACTIONS REQUIRED**

### Option A: Use Python Server (Recommended)
**Access URL**: `http://192.168.1.203:8080/`

1. **Transfer Updated Code**:
```bash
scp /home/lio/github/greenhouse-monitoring/beagleplay_code/ph_web_server.py debian@192.168.1.203:/home/debian/
```

2. **SSH to BeaglePlay and run**:
```bash
ssh debian@192.168.1.203
cd /home/debian
python3 ph_web_server.py
```

3. **Check the URL**: `http://192.168.1.203:8080/`
   - ✅ Dark mode
   - ✅ Timestamp
   - ✅ Landscape layout
   - ✅ Both BeagleConnect + Thermal data

### Option B: Fix Node-RED Dashboard
**Access URL**: `http://192.168.1.203:1880/ui`

1. **Import Node-RED Flow**:
   - Copy content of `node-red-dashboard-flow.json`
   - Go to Node-RED: `http://192.168.1.203:1880`
   - Menu → Import → Paste JSON
   - Deploy

2. **Features**:
   - ✅ Dark theme
   - ✅ Real-time updates
   - ✅ Timestamp display
   - ✅ Data from Python API

## 🔧 **Setting Up Auto-Start Service**

Once you confirm the Python server works, set up auto-start:

```bash
# SSH to BeaglePlay
ssh debian@192.168.1.203

# Create service file
sudo nano /etc/systemd/system/integrated-greenhouse.service
```

**Service file content**:
```ini
[Unit]
Description=Integrated Greenhouse Monitoring Dashboard
After=network.target
Wants=network.target

[Service]
Type=simple
User=debian
WorkingDirectory=/home/debian
ExecStart=/usr/bin/python3 /home/debian/ph_web_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable service**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable integrated-greenhouse.service
sudo systemctl start integrated-greenhouse.service
```

## 🔍 **Troubleshooting BeagleConnect Sensor Issues**

If sensors still show 0s, check:

1. **List IIO devices**:
```bash
ls -la /sys/bus/iio/devices/
```

2. **Check sensor files**:
```bash
# Look for temperature sensors
find /sys/bus/iio/devices/ -name "*temp*" -type f

# Look for humidity sensors  
find /sys/bus/iio/devices/ -name "*humidity*" -type f

# Look for pH sensors
find /sys/bus/iio/devices/ -name "*ph*" -type f
find /sys/bus/iio/devices/ -name "*voltage*" -type f
```

3. **Test reading values**:
```bash
# Test reading a sensor file directly
cat /sys/bus/iio/devices/iio:device0/in_temp_input
```

4. **Check logs**:
```bash
tail -f /home/debian/sensor_server.log
```

## 📡 **Network Independence Solution**

The Python server (port 8080) will work independently once:
1. Systemd service is running 
2. BeaglePlay boots with network connection
3. No laptop dependency

## ⚡ **Quick Test Commands**

```bash
# Test Python server accessibility
curl http://192.168.1.203:8080/

# Test API endpoint
curl http://192.168.1.203:8080/api/sensors

# Check service status
ssh debian@192.168.1.203 "sudo systemctl status integrated-greenhouse.service"
```

## 🎯 **Recommended Next Steps**

1. **First**: Test Option A (Python server on port 8080)
2. **If working**: Set up systemd service for auto-start
3. **Optional**: Configure Node-RED dashboard for additional features
4. **Test**: Power cycle BeaglePlay to ensure auto-start works

## 📞 **Support Commands**

```bash
# Service management
sudo systemctl start integrated-greenhouse.service    # Start
sudo systemctl stop integrated-greenhouse.service     # Stop  
sudo systemctl restart integrated-greenhouse.service  # Restart
sudo systemctl status integrated-greenhouse.service   # Status

# View logs
sudo journalctl -u integrated-greenhouse.service -f  # Follow logs
sudo journalctl -u integrated-greenhouse.service -n 50  # Last 50 lines
```

---

**🌟 Expected Result**: Dark mode dashboard with real-time BeagleConnect + thermal data, timestamps, and independent operation after disconnecting USB.
