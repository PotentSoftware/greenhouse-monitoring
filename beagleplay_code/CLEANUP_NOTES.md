# BeaglePlay Greenhouse System Cleanup

## Files Removed
- `ph_web_server_alt_port.py` - Redundant server that was running on port 8082

## Services Consolidated
- Updated `greenhouse-webserver.service` to point to the main `ph_web_server.py` on port 8080
- Removed duplicate service configurations

## Architecture Simplified
- **Main Dashboard**: http://192.168.1.203:8080/ (Python integrated dashboard)
- **Thermal Camera**: http://192.168.1.176/ (ESP32-S3 camera interface)  
- **Node-RED Editor**: http://192.168.1.203:1880/ (optional, for flow editing)
- **Node-RED Dashboard**: http://192.168.1.203:1880/ui (redundant, can be disabled)

## Node-RED Dashboard Issue
The Node-RED dashboard at /ui was showing duplicate data because:
1. It was configured to pull from both Python servers (port 8080 and 8082)
2. BeagleConnect Freedom data wasn't updating properly in Node-RED flows

## Recommendation
Since the Python integrated dashboard works perfectly, the Node-RED dashboard is redundant and can be:
- Disabled by stopping the Node-RED service
- Or kept running for advanced users who want to customize flows

## Current Status
- Single Python server on port 8080 with all thermal camera fixes
- Thermal camera fallback mechanism working
- System runs independently on dumb power supply
