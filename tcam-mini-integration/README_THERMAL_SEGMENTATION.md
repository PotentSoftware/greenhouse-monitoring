# tCam-Mini Thermal Segmentation System

A real-time thermal leaf segmentation visualization system for the tCam-Mini thermal camera with web-based monitoring interface.

## 🎯 Overview

This system provides:
- **Real-time thermal image capture** from tCam-Mini device
- **Automated leaf segmentation** using temperature thresholding and morphological filtering
- **Live web interface** with 4-panel visualization
- **Automatic device detection** with demo mode fallback
- **Region analysis** with temperature statistics

## 🏗️ Architecture

```
tCam-Mini Device (192.168.1.223)
         ↓
tcam_web_interface.py (Port 8080) ← Serves HTTP API
         ↓
thermal_web_simple.py (Port 5002) ← Analysis & Web UI
         ↓
Browser Interface (localhost:5002)
```

## 📋 Prerequisites

### Hardware
- tCam-Mini thermal camera
- Network connection to tCam-Mini device

### Software Dependencies
```bash
pip install opencv-python matplotlib flask requests pillow numpy
```

## 🚀 Quick Start

### 1. Start tCam Web Interface
```bash
cd tcam-mini-integration/scripts
python3 tcam_web_interface.py
```
This starts the HTTP API server on port 8080 that communicates with your tCam-Mini device.

### 2. Start Thermal Segmentation Viewer
```bash
python3 thermal_web_simple.py --tcam-ip 192.168.1.223 --port 5002
```

### 3. Access Web Interface
Open your browser to: **http://localhost:5002**

## 🔧 Configuration

### Network Settings
- **tCam-Mini Device IP**: `192.168.1.223`
- **tCam Web Interface**: Port `8080`
- **Thermal Viewer**: Port `5002`
- **Internal tCam Connection**: `192.168.1.130:5001`

### Command Line Options

#### thermal_web_simple.py
```bash
python3 thermal_web_simple.py [options]

Options:
  --tcam-ip IP      tCam-Mini device IP (default: 192.168.1.223)
  --port PORT       Web interface port (default: 5002)
```

## 📊 Features

### Real-Time Analysis
- **Temperature thresholding** for region detection
- **Morphological filtering** to clean noise
- **Connected components** analysis
- **Region statistics** (area, temperature, centroid)

### Web Interface
- **4-Panel Visualization**:
  - Original thermal image
  - Threshold mask
  - Cleaned mask  
  - Segmented regions with colored overlays
- **Live Statistics**: Temperature ranges, region counts
- **Auto-refresh** every 3 seconds
- **Connection status** indicator

### Automatic Fallback
- **Device Detection**: Scans ports 8080, 8081, 5000, 3000
- **Demo Mode**: Realistic simulated data when device unavailable
- **Robust Connection**: Handles network issues gracefully

## 🗂️ File Structure

### Core Scripts
- `tcam_web_interface.py` - HTTP API server for tCam-Mini
- `thermal_web_simple.py` - Main segmentation viewer with web interface
- `leaf_detection_prototype.py` - Original segmentation algorithm reference

### Diagnostic Tools
- `diagnose_tcam_connection.py` - Network connectivity diagnostics
- `find_tcam_device.py` - Device discovery utilities
- `quick_tcam_test.py` - Basic device communication test

### Output Directory
- `thermal_simple/` - Generated analysis images and data

## 🔍 Troubleshooting

### tCam-Mini Not Detected
1. **Check device IP**: Ensure tCam-Mini is at `192.168.1.223`
2. **Start web interface**: Run `tcam_web_interface.py` first
3. **Check connectivity**: Use diagnostic scripts
4. **Demo mode**: System automatically falls back if device unavailable

### Web Interface Issues
1. **Port conflicts**: Change port with `--port` option
2. **Browser cache**: Hard refresh (Ctrl+F5)
3. **Firewall**: Ensure ports 8080 and 5002 are accessible

### Analysis Problems
1. **No regions detected**: Check temperature thresholds in code
2. **Too many regions**: Adjust morphological filtering parameters
3. **Poor segmentation**: Verify thermal image quality

## 📈 Performance

- **Analysis Rate**: ~3 seconds per frame
- **Region Detection**: 0-200+ regions depending on scene
- **Memory Usage**: ~100MB typical
- **CPU Usage**: Moderate (single-threaded analysis)

## 🔮 Future Enhancements

- Integration with SAM2 segmentation model
- Multi-threading for faster analysis
- Historical data logging
- Advanced filtering algorithms
- Mobile-responsive interface
- REST API for external integration

## 📝 Development Notes

### Temperature Thresholding
- Default threshold: Mean + 1.5 * StdDev
- Morphological operations: Opening (3x3 kernel)
- Minimum region size: 50 pixels

### Visualization
- Colormap: 'hot' for thermal images
- Region colors: Random assignment
- Overlay transparency: 50%

## 🤝 Contributing

1. Test changes with both real device and demo mode
2. Maintain backward compatibility
3. Update documentation for configuration changes
4. Follow existing code style and structure

---

**Last Updated**: July 31, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅
