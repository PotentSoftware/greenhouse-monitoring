# Node-RED Dashboard Analysis

## Current Issue
The Node-RED dashboard at `http://192.168.1.203:1880/ui` is showing **duplicate data** and **BeagleConnect Freedom sensors are not updating**.

## Root Cause Analysis

### 1. Duplicate Data Display
The Node-RED dashboard was configured when there were two Python servers running:
- **Port 8080**: Main integrated dashboard (`ph_web_server.py`)
- **Port 8082**: Alternative server (`ph_web_server_alt_port.py`) - now removed

The Node-RED flows were likely pulling data from both endpoints, causing duplicate displays.

### 2. BeagleConnect Freedom Data Not Updating
Node-RED flows need to be configured to:
- Read from the correct IIO device paths
- Parse sensor data properly
- Update dashboard widgets with fresh data

## Resolution Options

### Option 1: Fix Node-RED Dashboard (Recommended for Advanced Users)
1. **Access Node-RED Editor**: http://192.168.1.203:1880/
2. **Update flows** to pull data from single Python server (port 8080)
3. **Fix sensor data reading** from IIO devices
4. **Remove duplicate widgets** and data sources
5. **Deploy updated flows**

### Option 2: Disable Node-RED Dashboard (Recommended for Most Users)
Since the Python integrated dashboard at port 8080 works perfectly:
1. **Keep Node-RED editor** for advanced flow customization
2. **Don't use Node-RED dashboard** - it's redundant
3. **Use Python dashboard** as primary interface

### Option 3: Completely Remove Node-RED
```bash
# Stop and disable Node-RED service
sudo systemctl stop node-red
sudo systemctl disable node-red
```

## Current Recommendation

**Use the Python integrated dashboard** at `http://192.168.1.203:8080/` as your primary interface because:

✅ **Working perfectly** with all features
✅ **Dark mode** optimized for greenhouse environments  
✅ **Real-time updates** for all sensors
✅ **Thermal camera integration** with fallback
✅ **VPD calculation** and display
✅ **Landscape layout** for tablet viewing
✅ **No duplicate data issues**

The Node-RED dashboard can be considered **optional/redundant** for this use case.

## URLs Summary

| URL | Purpose | Status | Recommendation |
|-----|---------|--------|----------------|
| `http://192.168.1.203:8080/` | Main Python Dashboard | ✅ Working | **PRIMARY - Use This** |
| `http://192.168.1.176/` | Thermal Camera | ✅ Working | Direct camera access |
| `http://192.168.1.203:1880/` | Node-RED Editor | ✅ Working | Optional for customization |
| `http://192.168.1.203:1880/ui` | Node-RED Dashboard | ⚠️ Duplicate data | Optional - can disable |
| `http://192.168.1.254/` | Router Management | N/A | Not part of project |
