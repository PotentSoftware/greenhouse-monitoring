# Precision Sensors Upgrade Implementation Plan

## Overview
This document outlines the major architectural refactor to replace BeagleConnect Freedom with precision sensors and upgrade the thermal camera system.

## Current System Analysis

### Current Architecture
- **BeaglePlay**: Central hub running Python web server (port 8080)
- **BeagleConnect Freedom**: Wireless sensors via Greybus/IIO (accuracy issues)
- **ESP32-S3 Thermal Camera**: MLX90640 at 192.168.1.176 (insufficient resolution)
- **Data Logging**: SD card storage with 5-minute intervals
- **Web Dashboard**: Real-time display with VPD calculations

### Current Sensor Reading Flow
1. `update_sensor_data()` function runs in background thread
2. Tries `read_greybus_i2c_sensors()` first (BeagleConnect Freedom)
3. Falls back to `find_iio_devices()` for direct IIO access
4. `fetch_thermal_data()` gets thermal camera data via HTTP
5. All data combined for VPD calculations and logging

## New Architecture Plan

### Hardware Changes
1. **Remove**: BeagleConnect Freedom entirely
2. **Add**: Feather S3[D] board with dual precision sensors
   - **I2C1 LDO1**: SHT45 (±0.1°C, ±1% RH accuracy)
   - **I2C2 LDO2**: HDC3022 (±0.1°C, ±2% RH accuracy)
3. **Replace**: ESP32-S3 thermal camera with tCam-mini Rev 4
   - **Sensor**: FLIR Lepton 3.5 (higher resolution)
   - **Connectivity**: WiFi with external antenna

### Software Architecture Changes

#### 1. Feather S3[D] Integration
**Communication Options:**
- **Option A**: HTTP REST API (recommended)
  - Feather S3[D] runs web server
  - BeaglePlay polls sensor data via HTTP
  - Easy debugging and monitoring
- **Option B**: MQTT (alternative)
  - Feather S3[D] publishes sensor data
  - BeaglePlay subscribes to topics
- **Option C**: Serial over USB (backup)
  - Direct serial communication
  - Requires physical connection

**Sensor Data Structure:**
```json
{
  "sht45": {
    "temperature": 23.45,
    "humidity": 58.2,
    "status": "ok"
  },
  "hdc3022": {
    "temperature": 23.41,
    "humidity": 58.7,
    "status": "ok"
  },
  "timestamp": "2025-07-24T18:30:00Z",
  "uptime": 12345
}
```

#### 2. tCam-mini Rev 4 Integration
**API Changes:**
- Update `fetch_thermal_data()` for new camera API
- Handle higher resolution thermal data
- Maintain existing thermal statistics calculations
- Support new camera features (if available)

**Expected API Differences:**
- Different HTTP endpoints
- Potentially different data formats
- Higher resolution thermal arrays
- Enhanced metadata

#### 3. BeaglePlay Python Server Updates

**Modified Functions:**
- `update_sensor_data()`: Remove BeagleConnect Freedom logic
- `fetch_feather_sensor_data()`: New function for Feather S3[D]
- `fetch_thermal_data()`: Update for tCam-mini Rev 4
- VPD calculations: Enhanced with dual sensor averaging

**New Features:**
- **Dual Sensor Averaging**: Combine SHT45 and HDC3022 readings
- **Sensor Health Monitoring**: Track individual sensor status
- **Fallback Logic**: Use single sensor if one fails
- **Configuration Management**: IP addresses, polling intervals

## Implementation Phases

### Phase 1: Feather S3[D] Firmware Development
**Deliverables:**
- Arduino/ESP-IDF firmware for Feather S3[D]
- Dual I2C sensor reading (SHT45 + HDC3022)
- HTTP REST API server
- WiFi connectivity and configuration
- Status LED indicators
- OTA update capability

**Key Files:**
- `feather-s3d-firmware/main.cpp`
- `feather-s3d-firmware/sensor_manager.h/cpp`
- `feather-s3d-firmware/web_server.h/cpp`
- `feather-s3d-firmware/config.h`

### Phase 2: BeaglePlay Integration
**Deliverables:**
- Updated `ph_web_server.py` with Feather S3[D] integration
- Remove BeagleConnect Freedom dependencies
- Enhanced sensor data processing
- Updated web dashboard
- Configuration management

**Key Changes:**
- Replace `read_greybus_i2c_sensors()` with `fetch_feather_sensor_data()`
- Remove `find_iio_devices()` dependency
- Add dual sensor averaging logic
- Update dashboard display for dual sensors

### Phase 3: tCam-mini Rev 4 Integration
**Deliverables:**
- Updated thermal camera integration
- Enhanced thermal data processing
- Maintain existing VPD calculations
- Support for higher resolution thermal data

**Key Changes:**
- Update `fetch_thermal_data()` for new camera API
- Handle new data formats
- Maintain backward compatibility with existing dashboard
- Enhanced thermal statistics if available

### Phase 4: Testing and Validation
**Deliverables:**
- Comprehensive testing suite
- Performance benchmarks
- Accuracy validation
- Documentation updates
- Migration guide

## Configuration Management

### Network Configuration
```json
{
  "feather_s3d": {
    "ip": "192.168.1.180",
    "port": 80,
    "endpoints": {
      "sensors": "/api/sensors",
      "status": "/api/status",
      "config": "/api/config"
    },
    "polling_interval": 5
  },
  "tcam_mini": {
    "ip": "192.168.1.181",
    "port": 80,
    "endpoints": {
      "thermal": "/api/thermal",
      "status": "/api/status"
    },
    "polling_interval": 2
  }
}
```

### Sensor Configuration
```json
{
  "sensors": {
    "temperature": {
      "primary": "sht45",
      "secondary": "hdc3022",
      "averaging": true,
      "tolerance": 0.5
    },
    "humidity": {
      "primary": "sht45", 
      "secondary": "hdc3022",
      "averaging": true,
      "tolerance": 2.0
    }
  }
}
```

## Migration Strategy

### Development Approach
1. **Create new branch**: `precision-sensors-upgrade`
2. **Parallel development**: Keep existing system functional
3. **Incremental testing**: Test each component separately
4. **Staged deployment**: Phase-by-phase implementation
5. **Rollback capability**: Maintain existing system as backup

### Testing Strategy
1. **Unit Testing**: Individual sensor reading functions
2. **Integration Testing**: Full system with new hardware
3. **Performance Testing**: Response times and accuracy
4. **Stress Testing**: Long-term operation and error handling
5. **Validation Testing**: Compare with reference sensors

## Expected Benefits

### Accuracy Improvements
- **Temperature**: ±0.1°C vs current inaccuracies
- **Humidity**: ±1-2% RH vs current inaccuracies
- **Thermal Resolution**: Higher resolution canopy temperature measurement
- **Dual Sensor Redundancy**: Cross-validation and averaging

### Operational Improvements
- **Modular pH System**: Easy calibration without system disruption
- **Better Thermal Imaging**: Higher resolution for early growth stages
- **Simplified Architecture**: Remove complex Greybus dependencies
- **Enhanced Reliability**: Fewer wireless communication issues

### Maintenance Benefits
- **Easier Debugging**: HTTP APIs vs complex Greybus protocols
- **Better Monitoring**: Individual sensor health status
- **Simplified Updates**: Standard ESP32 OTA vs firmware flashing
- **Reduced Complexity**: Fewer system dependencies

## Risk Mitigation

### Technical Risks
- **Hardware Compatibility**: Validate all sensor interfaces
- **Network Reliability**: Implement robust error handling
- **Power Management**: Ensure stable operation
- **Integration Complexity**: Thorough testing required

### Mitigation Strategies
- **Prototype Testing**: Build and test before full implementation
- **Fallback Options**: Maintain existing system during transition
- **Documentation**: Comprehensive setup and troubleshooting guides
- **Monitoring**: Enhanced logging and status reporting

## Timeline Estimate

- **Phase 1 (Feather S3[D])**: 2-3 weeks
- **Phase 2 (BeaglePlay)**: 1-2 weeks  
- **Phase 3 (tCam-mini)**: 1-2 weeks
- **Phase 4 (Testing)**: 1-2 weeks
- **Total**: 5-9 weeks

## Success Criteria

1. **Accuracy**: Temperature within ±0.2°C of reference
2. **Reliability**: >99% uptime over 30 days
3. **Performance**: <5 second response times
4. **Functionality**: All existing features maintained
5. **Usability**: Simplified maintenance and calibration

---

*This plan will be updated as implementation progresses and requirements are refined.*