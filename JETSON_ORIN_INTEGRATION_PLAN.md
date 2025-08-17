# Jetson Orin Nano Integration Plan

## Overview
Create an independent greenhouse monitoring system on the Jetson Orin Nano that operates concurrently with the BeaglePlay, providing redundancy and enhanced processing capabilities.

## System Architecture

### Hardware Components
- **Jetson Orin Nano**: Main processing unit (192.168.1.75)
- **Feather S3[D]**: Dual precision sensors (SHT45 + HDC3022) at 192.168.1.81
- **tCam-Mini**: Thermal camera at 192.168.1.130
- **Network**: All devices on same WiFi network (BT-X6F962)

### Software Stack
- **Python 3.8+**: Main programming language
- **Flask**: Web server framework
- **OpenCV**: Image processing (future enhancement)
- **NumPy/SciPy**: Numerical computations
- **Matplotlib**: Visualization
- **Requests**: HTTP communication

## Key Features

### 1. Independent Operation
- No dependency on BeaglePlay
- Separate data collection and processing
- Independent web dashboard on port 8082
- Autonomous system recovery

### 2. Sensor Integration
- HTTP API communication with Feather S3[D]
- Socket API communication with tCam-Mini
- Real-time data collection every 5 seconds
- Fallback mechanisms for connectivity issues

### 3. Thermal Processing
- Raw thermal image acquisition from tCam-Mini
- Canopy temperature calculation using current algorithm
- Statistical analysis (min, max, mean, median, mode)
- Negative pixel filtering for data quality

### 4. VPD Calculations
- Air VPD: Using averaged sensor temperature + humidity
- Canopy VPD: Using thermal temperature + air humidity
- Enhanced VPD: Average of Air + Canopy VPD
- Thermal VPD: Pure thermal-based calculation

### 5. Web Dashboard
- Similar interface to BeaglePlay dashboard
- Real-time sensor displays
- Enhanced VPD calculations with thermal data
- Thermal image visualization
- Data export capabilities

### 6. Future OpenCV Integration
- Modular image processing framework
- Pluggable processing strategies
- Advanced leaf segmentation algorithms
- Machine learning integration ready

## Implementation Phases

### Phase 1: Basic System Setup
1. Jetson environment configuration
2. Python dependencies installation
3. Network connectivity verification
4. Basic sensor communication testing

### Phase 2: Core Integration
1. Feather S3[D] HTTP API integration
2. tCam-Mini socket communication
3. Basic thermal image processing
4. VPD calculation implementation

### Phase 3: Web Interface
1. Flask web server setup
2. Dashboard HTML/CSS/JavaScript
3. Real-time data display
4. Thermal image visualization

### Phase 4: Advanced Features
1. Data logging and export
2. System monitoring and health checks
3. Error handling and recovery
4. Performance optimization

### Phase 5: OpenCV Framework
1. Modular image processing architecture
2. Advanced thermal analysis algorithms
3. Leaf detection and segmentation
4. Machine learning integration

## Directory Structure
```
jetson-orin-integration/
├── src/
│   ├── jetson_greenhouse_server.py    # Main server application
│   ├── sensor_manager.py              # Sensor communication
│   ├── thermal_processor.py           # Thermal image processing
│   ├── vpd_calculator.py              # VPD calculations
│   └── web_interface.py               # Web dashboard
├── templates/
│   └── dashboard.html                 # Web interface template
├── static/
│   ├── css/
│   └── js/
├── config/
│   └── jetson_config.py               # Configuration settings
├── tests/
│   └── test_integration.py            # Integration tests
├── requirements.txt                   # Python dependencies
├── install.sh                         # Installation script
└── README.md                          # Documentation
```

## Network Configuration
- **Jetson Orin Nano**: 192.168.1.75:8082 (web dashboard)
- **BeaglePlay**: 192.168.1.203:8080 (existing system)
- **Feather S3[D]**: 192.168.1.81:8080 (sensor API)
- **tCam-Mini**: 192.168.1.130:5001 (socket API)

## Concurrent Operation Strategy
1. **Port Separation**: Jetson uses 8082, BeaglePlay uses 8080
2. **Independent Data Sources**: Both systems read from same sensors
3. **No Interference**: Systems operate without affecting each other
4. **Redundancy**: Loss of one system doesn't affect the other
5. **Comparison**: Both systems can be monitored simultaneously

## Benefits
- **Redundancy**: Backup system if BeaglePlay fails
- **Performance**: Jetson's superior processing power
- **Scalability**: Foundation for advanced AI/ML features
- **Development**: Safe testing environment for new features
- **Comparison**: Validate data consistency between systems
