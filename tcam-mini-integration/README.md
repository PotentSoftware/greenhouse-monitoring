# tCam-Mini-Rev 4 Integration with Advanced Leaf Analysis

## Overview

This directory contains the implementation for replacing the current ESP32-S3 + MLX90640 thermal camera with a tCam-Mini-Rev 4 + FLIR Lepton 3.5 system that provides:

- **20x Resolution Improvement**: From 32×24 to 160×120 pixels
- **Professional Thermal Sensor**: FLIR Lepton 3.5 vs consumer MLX90640  
- **Advanced Leaf Analysis**: Individual leaf identification and temperature statistics
- **Population-Level Analytics**: Statistics across all detected leaves
- **Enhanced VPD Calculations**: Using leaf-specific temperature data

## 🎉 Status: WIRELESS DEPLOYMENT COMPLETE! ✅

**MAJOR SUCCESS**: The tCam-Mini has been successfully deployed in wireless station mode with full functionality!

### 🌐 Wireless Operation Achieved:
- ✅ **Station Mode Firmware**: Custom WiFi configuration deployed
- ✅ **Home Network Integration**: Connected to BT-X6F962 at 192.168.1.130
- ✅ **Internet Connectivity Preserved**: No more network switching required
- ✅ **USB Independence**: Full wireless operation with external power
- ✅ **Real-World Deployment**: Camera repositioned and tested successfully

## Quick Start

### 1. Hardware Setup
- Connect tCam-Mini-Rev 4 to USB hub and power up
- Verify LED indicators show normal operation
- Install tCam desktop software for initial testing

### 2. Thermal Segmentation System (Production Ready)
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts/

# Start tCam web interface (required first)
python3 tcam_web_interface.py

# Start thermal segmentation viewer
python3 thermal_web_simple.py --tcam-ip 192.168.1.223 --port 5002

# Access web interface at: http://localhost:5002
```

### 3. Basic Testing & Diagnostics
```bash
# Test basic communication with tCam-Mini
python3 tcam_basic_test.py

# Capture and analyze thermal images  
python3 tcam_image_capture.py

# Test leaf detection algorithms
python3 leaf_detection_prototype.py
```

### 4. Development Environment
```bash
# Install required packages
pip install opencv-python numpy scipy scikit-image requests pillow matplotlib
```

## Project Structure

```
tcam-mini-integration/
├── README.md                          # This file
├── README_THERMAL_SEGMENTATION.md     # 🔥 Thermal segmentation system docs
├── IMPLEMENTATION_PLAN.md             # Detailed implementation plan
├── GETTING_STARTED.md                # Step-by-step getting started guide
├── scripts/                          # Development and testing scripts
│   ├── tcam_web_interface.py         # ✅ tCam HTTP API server (port 8080)
│   ├── thermal_web_simple.py         # ✅ Main segmentation viewer (port 5002)
│   ├── leaf_detection_prototype.py   # Computer vision prototype
│   ├── tcam_basic_test.py            # Basic tCam-Mini communication test
│   ├── tcam_image_capture.py         # Image capture and analysis
│   └── thermal_simple/               # Generated analysis output
├── test_images/                      # Captured thermal images
├── docs/                             # Documentation
└── cv_development/                   # Computer vision development
```

## Implementation Phases

### 🎉 **THERMAL SEGMENTATION SYSTEM - COMPLETE!** ✅
**Real-time thermal leaf segmentation with web interface is production ready!**
- [x] tCam-Mini HTTP API server (`tcam_web_interface.py`)
- [x] Real-time segmentation viewer (`thermal_web_simple.py`) 
- [x] Auto-detection with demo fallback
- [x] 4-panel visualization with live statistics
- [x] Web interface at http://localhost:5002
- [x] **See: `README_THERMAL_SEGMENTATION.md` for full documentation**

### Phase 1: Basic Setup ✅ (Complete)
- [x] Hardware connection and power-up
- [x] Basic communication testing scripts
- [x] Image capture and analysis tools
- [x] tCam-Mini API documentation and testing

### Phase 2: Communication ✅ (Complete)
- [x] HTTP API communication with tCam-Mini
- [x] Reliable image transfer and processing
- [x] Web-based interface for monitoring

### Phase 3: Computer Vision ✅ (Complete)
- [x] Leaf detection algorithm prototype
- [x] Real-time segmentation with morphological filtering
- [x] Connected components analysis
- [x] Region visualization with colored overlays

### Phase 4: Temperature Analysis ✅ (Complete)
- [x] Per-region temperature statistics
- [x] Population-level analysis
- [x] Real-time thermal data integration

### Phase 5: System Integration (Week 4-5)
- [ ] Enhanced VPD calculations using leaf temperatures
- [ ] Dashboard updates with leaf analysis
- [ ] API extensions for advanced data

### Phase 6: Production Deployment (Week 5-6)
- [ ] Wireless operation with dumb power supply
- [ ] Performance optimization
- [ ] Long-term reliability testing

## Key Features to Implement

### 1. Leaf Identification
- Temperature-based segmentation to separate leaves from background
- Morphological operations to clean noise and fill gaps
- Shape and size filtering to validate leaf-like regions
- Connected component analysis to identify individual leaves

### 2. Per-Leaf Temperature Analysis
For each detected leaf:
- Number of temperature measurements (pixels)
- Minimum and maximum temperatures
- Mean, median, mode, and standard deviation
- Centroid and bounding box coordinates

### 3. Population-Level Statistics
Across all detected leaves:
- Total number of leaves in field of view
- Overall temperature statistics (min, max, mean, median, mode, std dev)
- Temperature distribution analysis
- Spatial distribution of leaves

### 4. Enhanced VPD Calculations
- Air VPD: Air temperature + air humidity
- Average Leaf VPD: Mean leaf temperature + air humidity
- Max Leaf VPD: Hottest leaf + air humidity (stress indicator)
- Min Leaf VPD: Coolest leaf + air humidity (optimal growth)
- Per-leaf VPD: Individual VPD for each detected leaf

## Expected Data Structure

```json
{
  "timestamp": "2025-07-27T10:00:00Z",
  "image_info": {
    "resolution": "160x120",
    "total_pixels": 19200,
    "camera_temp": 25.2
  },
  "leaf_analysis": {
    "total_leaves_detected": 15,
    "individual_leaves": [
      {
        "leaf_id": 1,
        "pixel_count": 245,
        "min_temp": 22.1,
        "max_temp": 24.8,
        "mean_temp": 23.4,
        "median_temp": 23.3,
        "mode_temp": 23.2,
        "std_dev_temp": 0.8,
        "centroid": [80, 60],
        "bounding_box": [70, 50, 90, 70]
      }
    ],
    "population_statistics": {
      "total_measurements": 3680,
      "overall_min_temp": 21.8,
      "overall_max_temp": 25.2,
      "overall_mean_temp": 23.6,
      "overall_median_temp": 23.5,
      "overall_mode_temp": 23.4,
      "overall_std_dev_temp": 1.2
    }
  },
  "enhanced_vpd": {
    "air_vpd": 1.2,
    "average_leaf_vpd": 1.1,
    "max_leaf_vpd": 1.3,
    "min_leaf_vpd": 0.9,
    "per_leaf_vpd": [1.1, 1.0, 1.2, ...]
  }
}
```

## Current Status

**Hardware**: tCam-Mini-Rev 4 connected and ready for testing
**Software**: Basic testing scripts created and ready to run
**Next Step**: Run `tcam_basic_test.py` to discover tCam-Mini API endpoints

## Getting Help

1. **Hardware Issues**: Check GETTING_STARTED.md troubleshooting section
2. **Software Issues**: Review script comments and error messages
3. **Computer Vision**: Tune parameters in leaf_detection_prototype.py
4. **Integration**: Follow IMPLEMENTATION_PLAN.md phase-by-phase

## Success Metrics

- **Leaf Detection Accuracy**: >90% correct identification
- **Temperature Accuracy**: ±0.5°C measurement precision
- **Processing Speed**: 1-5 Hz real-time analysis
- **System Reliability**: 99%+ uptime in production

---

**Start Here**: Run `python3 scripts/tcam_basic_test.py` to begin testing your tCam-Mini!