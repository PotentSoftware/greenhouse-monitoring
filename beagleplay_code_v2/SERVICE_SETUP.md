# Precision Sensors Server - Automatic Startup Service

This document explains how to set up the Precision Sensors Server to start automatically on boot with proper port cleanup.

## Overview

The automatic startup system consists of:

1. **`start_precision_server.sh`** - Smart startup script with port cleanup
2. **`precision-sensors.service`** - Systemd service configuration
3. **`install_service.sh`** - Installation script

## Features

### ✅ **Port Cleanup**
- Automatically detects and kills processes using port 8080
- Handles hangover processes from previous runs
- Ensures clean startup every time

### ✅ **Process Management**
- Kills existing `precision_sensors_server.py` processes
- Waits for graceful shutdown before force-killing
- Comprehensive logging of all actions

### ✅ **Robust Startup**
- Verifies server script exists before starting
- Checks port availability after cleanup
- Confirms server is running and listening
- Detailed startup logging with timestamps

### ✅ **Automatic Restart**
- Service restarts automatically if it crashes
- 15-second delay between restart attempts
- Systemd manages the service lifecycle

## Installation

### Step 1: Copy Files to BeaglePlay

The following files should already be copied to the BeaglePlay:

```bash
# Files on BeaglePlay:
/home/debian/precision_sensors_server.py    # Main server script
/home/debian/start_precision_server.sh      # Startup script (executable)
/tmp/precision-sensors.service              # Systemd service file
/home/debian/install_service.sh             # Installation script (executable)
```

### Step 2: Install the Service

Run the installation script **with sudo**:

```bash
# On BeaglePlay:
cd /home/debian
sudo ./install_service.sh
```

The installation script will:
- Stop any existing services
- Install the new systemd service
- Enable automatic startup on boot
- Start the service immediately
- Show service status and management commands

## Service Management

### Basic Commands

```bash
# Start the service
sudo systemctl start precision-sensors.service

# Stop the service
sudo systemctl stop precision-sensors.service

# Restart the service
sudo systemctl restart precision-sensors.service

# Check service status
sudo systemctl status precision-sensors.service

# Enable automatic startup (done during installation)
sudo systemctl enable precision-sensors.service

# Disable automatic startup
sudo systemctl disable precision-sensors.service
```

### Viewing Logs

```bash
# View systemd service logs (live)
sudo journalctl -u precision-sensors.service -f

# View startup script logs
cat /home/debian/precision_server_startup.log

# View server application logs
cat /home/debian/precision_server.log
```

## Log Files

### 1. Startup Log: `/home/debian/precision_server_startup.log`

Contains detailed startup sequence with timestamps:
```
2025-07-26 11:36:18 - 🚀 Starting Precision Sensors Server startup sequence
2025-07-26 11:36:18 - 🧹 Starting cleanup sequence
2025-07-26 11:36:18 - 🔍 Checking for existing precision_sensors_server.py processes
2025-07-26 11:36:18 - ✅ No existing server processes found
2025-07-26 11:36:18 - 🔍 Checking for processes using port 8080
2025-07-26 11:36:18 - ✅ Port 8080 is free
2025-07-26 11:36:21 - 🌱 Starting Precision Sensors Server
2025-07-26 11:36:26 - ✅ Precision Sensors Server started successfully (PID: 3195)
2025-07-26 11:36:26 - 🎉 Startup sequence completed successfully
```

### 2. Server Log: `/home/debian/precision_server.log`

Contains server application logs:
```
2025-07-26 11:36:26,123 - INFO - 🌱 Starting Precision Sensors Server v3.0
2025-07-26 11:36:26,124 - INFO - ✅ Sensor update thread started
2025-07-26 11:36:26,125 - INFO - 🚀 HTTP server starting on port 8080
```

### 3. Systemd Logs

View with `journalctl`:
```bash
sudo journalctl -u precision-sensors.service --no-pager -l
```

## Troubleshooting

### Service Won't Start

1. **Check service status:**
   ```bash
   sudo systemctl status precision-sensors.service
   ```

2. **Check startup logs:**
   ```bash
   cat /home/debian/precision_server_startup.log
   ```

3. **Check for port conflicts:**
   ```bash
   sudo lsof -i:8080
   ```

4. **Manual cleanup and restart:**
   ```bash
   sudo pkill -f precision_sensors_server.py
   sudo systemctl restart precision-sensors.service
   ```

### Port 8080 Still Blocked

The startup script should handle this automatically, but if needed:

```bash
# Find processes using port 8080
sudo lsof -i:8080

# Kill specific process
sudo kill -9 <PID>

# Or kill all processes using the port
sudo fuser -k 8080/tcp
```

### Service Keeps Restarting

1. **Check server logs for errors:**
   ```bash
   tail -50 /home/debian/precision_server.log
   ```

2. **Check if dependencies are available:**
   ```bash
   # Feather S3[D] should be reachable
   curl -s http://192.168.1.81/sensors
   
   # Thermal camera should be reachable
   curl -s http://192.168.1.176/thermal_data
   ```

3. **Temporarily disable restart to debug:**
   ```bash
   sudo systemctl edit precision-sensors.service
   # Add: [Service]
   #      Restart=no
   ```

## File Structure

```
/home/debian/
├── precision_sensors_server.py          # Main server application
├── start_precision_server.sh            # Startup script with port cleanup
├── install_service.sh                   # Service installation script
├── precision_server_startup.log         # Startup sequence log
└── precision_server.log                 # Server application log

/etc/systemd/system/
└── precision-sensors.service            # Systemd service configuration

/tmp/
└── precision-sensors.service            # Service file (temporary location)
```

## Service Configuration Details

The systemd service (`precision-sensors.service`) is configured with:

- **Type**: `forking` - Allows the startup script to background the server
- **User**: `debian` - Runs as the debian user (not root)
- **Restart**: `always` - Automatically restarts if the service fails
- **RestartSec**: `15` - Waits 15 seconds between restart attempts
- **TimeoutStartSec**: `60` - Allows up to 60 seconds for startup

## Security Notes

- Service runs as the `debian` user (not root)
- No elevated privileges required for normal operation
- Startup script only needs access to kill processes and bind to port 8080
- All log files are owned by the `debian` user

## Dashboard Access

Once the service is running, the dashboard is available at:
- **URL**: http://192.168.1.203:8080/
- **Plots**: http://192.168.1.203:8080/plots
- **API**: http://192.168.1.203:8080/api/sensors

## Integration Status

The service integrates with:
- **Feather S3[D]**: http://192.168.1.81/ (dual sensors)
- **Thermal Camera**: http://192.168.1.176/ (ESP32-S3)
- **Data Logging**: CSV files on SD card
- **Web Dashboard**: Real-time monitoring interface
