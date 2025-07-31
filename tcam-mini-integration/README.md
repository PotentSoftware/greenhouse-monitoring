# tCam-Mini-Rev 4 Integration with Advanced Leaf Analysis

## Overview

This directory contains the implementation for replacing the current ESP32-S3 + MLX90640 thermal camera with a tCam-Mini-Rev 4 + FLIR Lepton 3.5 system that provides:

- **20x Resolution Improvement**: From 32×24 to 160×120 pixels
- **Professional Thermal Sensor**: FLIR Lepton 3.5 vs consumer MLX90640  
- **Advanced Leaf Analysis**: Individual leaf identification and temperature statistics
- **Population-Level Analytics**: Statistics across all detected leaves
- **Enhanced VPD Calculations**: Using leaf-specific temperature data

## Quick Start

### 1. Hardware Setup
- Connect tCam-Mini-Rev 4 to USB hub and power up
- Verify LED indicators show normal operation
- Install tCam desktop software for initial testing

### 2. Basic Testing
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts/

# Test basic communication with tCam-Mini
python3 tcam_basic_test.py

# Capture and analyze thermal images  
python3 tcam_image_capture.py

# Test leaf detection algorithms
python3 leaf_detection_prototype.py
```

### 3. Development Environment
```bash
# Install required packages
pip install opencv-python numpy scipy scikit-image requests pillow matplotlib
```

## Project Structure

```
tcam-mini-integration/
├── README.md                     # This file
├── IMPLEMENTATION_PLAN.md        # Detailed implementation plan
├── GETTING_STARTED.md           # Step-by-step getting started guide
├── scripts/                     # Development and testing scripts
│   ├── tcam_basic_test.py       # Basic tCam-Mini communication test
│   ├── tcam_image_capture.py    # Image capture and analysis
│   └── leaf_detection_prototype.py # Computer vision prototype
├── test_images/                 # Captured thermal images (created during testing)
├── docs/                        # Documentation (to be created)
└── cv_development/              # Computer vision development (to be created)
```

## Implementation Phases

### Phase 1: Basic Setup ✅ (Ready to Start)
- [x] Hardware connection and power-up
- [x] Basic communication testing scripts
- [x] Image capture and analysis tools
- [ ] **YOUR TASK**: Run basic tests and document tCam-Mini API

### Phase 2: Communication (Week 1-2)
- [ ] WiFi configuration and network setup
- [ ] Reliable image transfer to BeaglePlay
- [ ] Integration with existing precision_sensors_server.py

### Phase 3: Computer Vision (Week 2-3)
- [x] Leaf detection algorithm prototype
- [ ] Parameter tuning for greenhouse conditions
- [ ] Validation with real greenhouse images

### Phase 4: Temperature Analysis (Week 3-4)
- [x] Per-leaf statistics calculation
- [x] Population-level analysis
- [ ] Integration with thermal data from tCam-Mini

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