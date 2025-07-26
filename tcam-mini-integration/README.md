# tCam-mini Rev 4 Integration Guide

## Overview
This document outlines the integration of the tCam-mini Rev 4 thermal camera with FLIR Lepton 3.5 sensor into the greenhouse monitoring system.

## Hardware Specifications

### tCam-mini Rev 4
- **Product**: https://groupgets.com/products/tcam-mini-rev4-wireless-streaming-thermal-camera-board
- **Thermal Sensor**: FLIR Lepton 3.5
- **Resolution**: 160x120 pixels (vs 32x24 on MLX90640)
- **Temperature Range**: -10°C to +400°C
- **Accuracy**: ±5°C or ±5% (whichever is greater)
- **Connectivity**: WiFi 802.11b/g/n
- **External Antenna**: Improved range and reliability

### Key Improvements over ESP32-S3 + MLX90640
1. **Higher Resolution**: 160x120 vs 32x24 pixels (20x improvement)
2. **Better Accuracy**: Professional FLIR sensor vs consumer MLX90640
3. **Wider Temperature Range**: -10°C to +400°C vs -40°C to +300°C
4. **Enhanced Connectivity**: External antenna for better WiFi performance
5. **Professional Grade**: Industrial thermal imaging vs hobbyist sensor

## Software Integration

### Expected API Differences
The tCam-mini Rev 4 likely uses different API endpoints and data formats compared to our current ESP32-S3 implementation:

#### Current ESP32-S3 API (to be replaced):
```
GET /thermal_data
{
  "minTemp": 18.5,
  "maxTemp": 32.1,
  "meanTemp": 25.3,
  "medianTemp": 24.8,
  "rangeTemp": 13.6,
  "modeTemp": 24.2,
  "stdDevTemp": 3.2,
  "status": "ok"
}
```

#### Expected tCam-mini API (based on GitHub examples):
```
GET /api/thermal
{
  "thermal_data": {
    "min_temperature": 18.5,
    "max_temperature": 32.1,
    "mean_temperature": 25.3,
    "median_temperature": 24.8,
    "std_dev_temperature": 3.2,
    "pixel_data": [...], // 160x120 array
    "timestamp": "2025-07-24T18:30:00Z"
  },
  "camera_info": {
    "model": "FLIR Lepton 3.5",
    "resolution": "160x120",
    "fpa_temp": 25.2,
    "housing_temp": 24.8
  },
  "status": "ok"
}
```

### Integration Points

#### 1. BeaglePlay Python Server Updates
The `fetch_tcam_thermal_data()` function needs updates for:
- New API endpoints
- Different JSON key names
- Enhanced thermal data processing
- Higher resolution pixel data handling

#### 2. Enhanced Statistics
With 160x120 resolution (19,200 pixels vs 768), we can calculate:
- More accurate temperature statistics
- Spatial temperature analysis
- Hot/cold spot detection
- Temperature gradients across canopy
- Zone-based temperature monitoring

#### 3. VPD Calculation Improvements
Higher resolution enables:
- Multiple canopy zones for VPD calculation
- Plant-specific temperature monitoring
- Growth stage adaptive monitoring
- Precision irrigation targeting

## Implementation Plan

### Phase 1: Hardware Setup
1. **Network Configuration**
   - Configure tCam-mini WiFi settings
   - Assign static IP address (192.168.1.185)
   - Test basic connectivity and web interface

2. **API Discovery**
   - Explore available endpoints
   - Document actual API format
   - Test data retrieval and parsing
   - Verify update rates and reliability

### Phase 2: Software Integration
1. **Update BeaglePlay Server**
   - Modify `fetch_tcam_thermal_data()` function
   - Handle new API format and endpoints
   - Implement enhanced statistics calculation
   - Add error handling for new camera

2. **Enhanced Dashboard**
   - Update thermal camera section
   - Add higher resolution data display
   - Implement zone-based temperature monitoring
   - Enhanced VPD calculations with spatial data

### Phase 3: Advanced Features
1. **Spatial Analysis**
   - Zone-based temperature monitoring
   - Hot/cold spot detection
   - Temperature gradient analysis
   - Plant growth tracking

2. **Enhanced VPD**
   - Multi-zone VPD calculations
   - Plant-specific VPD monitoring
   - Adaptive irrigation recommendations
   - Growth stage optimization

## Configuration Files

### Network Configuration
```json
{
  "tcam_mini": {
    "ip_address": "192.168.1.185",
    "subnet_mask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "dns": "8.8.8.8",
    "wifi_ssid": "greenhouse_network",
    "wifi_password": "your_password"
  }
}
```

### API Configuration
```json
{
  "endpoints": {
    "thermal_data": "/api/thermal",
    "camera_status": "/api/status",
    "camera_config": "/api/config",
    "live_stream": "/api/stream",
    "thermal_image": "/api/image"
  },
  "polling": {
    "interval_seconds": 2,
    "timeout_seconds": 5,
    "retry_count": 3
  }
}
```

## Code Examples

### Updated Thermal Data Fetching
```python
def fetch_tcam_thermal_data():
    """Fetch thermal camera data from tCam-mini Rev 4"""
    try:
        url = f"http://{TCAM_MINI_CONFIG['primary_ip']}/api/thermal"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            thermal_data = data.get('thermal_data', {})
            
            # Extract enhanced thermal statistics
            thermal_min_temp = thermal_data.get('min_temperature', 0.0)
            thermal_max_temp = thermal_data.get('max_temperature', 0.0)
            thermal_mean_temp = thermal_data.get('mean_temperature', 0.0)
            thermal_std_dev_temp = thermal_data.get('std_dev_temperature', 0.0)
            
            # Process pixel data for advanced analysis
            pixel_data = thermal_data.get('pixel_data', [])
            if pixel_data:
                # Calculate additional statistics from high-res data
                thermal_median_temp = calculate_median(pixel_data)
                thermal_mode_temp = calculate_mode(pixel_data)
                hot_spots = detect_hot_spots(pixel_data)
                cold_spots = detect_cold_spots(pixel_data)
            
            return True
    except Exception as e:
        logging.error(f"Error fetching tCam-mini data: {e}")
        return False
```

### Enhanced VPD with Spatial Data
```python
def calculate_enhanced_vpd_zones(pixel_data, air_temp, humidity):
    """Calculate VPD for different canopy zones"""
    zones = divide_into_zones(pixel_data)  # e.g., 4x4 grid
    vpd_zones = {}
    
    for zone_name, zone_pixels in zones.items():
        zone_temp = np.mean(zone_pixels)
        svp_canopy = 0.6108 * math.exp(17.27 * zone_temp / (zone_temp + 237.3))
        svp_air = 0.6108 * math.exp(17.27 * air_temp / (air_temp + 237.3))
        avp = svp_air * (humidity / 100)
        vpd_zones[zone_name] = svp_canopy - avp
    
    return vpd_zones
```

## Testing and Validation

### Hardware Testing
1. **Connectivity Tests**
   - WiFi connection stability
   - API response times
   - Data accuracy validation
   - Temperature calibration

2. **Performance Tests**
   - Update rate consistency
   - Network reliability
   - Power consumption
   - Operating temperature range

### Software Testing
1. **Integration Tests**
   - API compatibility
   - Data parsing accuracy
   - Error handling robustness
   - Dashboard display correctness

2. **Accuracy Tests**
   - Compare with reference thermometer
   - Validate statistics calculations
   - Test VPD calculation accuracy
   - Verify spatial analysis features

## Migration Strategy

### From ESP32-S3 to tCam-mini
1. **Parallel Operation**
   - Run both cameras simultaneously during testing
   - Compare data accuracy and reliability
   - Validate enhanced features

2. **Gradual Transition**
   - Update API endpoints with fallback support
   - Test enhanced features incrementally
   - Maintain backward compatibility during transition

3. **Full Migration**
   - Remove ESP32-S3 dependencies
   - Optimize for tCam-mini features
   - Update documentation and user guides

## Expected Benefits

### Accuracy Improvements
- **Higher Resolution**: 20x more thermal pixels for detailed analysis
- **Professional Sensor**: FLIR Lepton 3.5 vs consumer MLX90640
- **Better Calibration**: Factory-calibrated professional thermal sensor
- **Spatial Analysis**: Zone-based temperature monitoring

### Operational Benefits
- **Early Growth Monitoring**: Higher resolution enables monitoring of small plants
- **Precision VPD**: Multiple canopy zones for targeted irrigation
- **Plant Health**: Detect stress patterns across canopy
- **Growth Optimization**: Track temperature patterns during different growth stages

### System Benefits
- **Reliability**: Professional-grade hardware
- **Expandability**: Rich API for future enhancements
- **Integration**: Better WiFi connectivity with external antenna
- **Maintenance**: Fewer calibration requirements

---

*This integration guide will be updated as implementation progresses and actual tCam-mini API is discovered.*