# Feather S3[D] Precision Sensor Firmware

## Overview
This firmware runs on the Feather S3[D] board and provides high-precision temperature and humidity measurements using dual sensors connected via STEMMA/QT connectors.

## Hardware Configuration

### Board: Feather S3[D]
- **Product**: https://unexpectedmaker.com/shop.html#!/FeatherS3-D/p/759221736
- **MCU**: ESP32-S3 with dual-core processor
- **WiFi**: 2.4GHz 802.11b/g/n
- **I2C**: Two independent I2C buses with LDO power supplies

### Sensors

#### I2C1 LDO1: SHT45 Precision Sensor
- **Product**: https://shop.pimoroni.com/products/adafruit-sensirion-sht45-precision-temperature-humidity-sensor-stemma-qt-qwiic?variant=40478018011219
- **Accuracy**: ±0.1°C temperature, ±1% RH humidity
- **Resolution**: 0.01°C temperature, 0.01% RH humidity
- **I2C Address**: 0x44 (default)

#### I2C2 LDO2: HDC3022 Precision Sensor
- **Product**: https://shop.pimoroni.com/products/adafruit-hdc3022-precision-temperature-humidity-sensor-stemma-qt-qwiic?variant=53511776698747
- **Accuracy**: ±0.1°C temperature, ±2% RH humidity  
- **Resolution**: 0.01°C temperature, 0.01% RH humidity
- **I2C Address**: 0x44 (default, but on separate bus)

## Features

### Core Functionality
- **Dual Sensor Reading**: Independent I2C buses prevent conflicts
- **HTTP REST API**: Easy integration with BeaglePlay
- **WiFi Connectivity**: Automatic connection and reconnection
- **Status Monitoring**: Individual sensor health tracking
- **Error Handling**: Graceful degradation if one sensor fails

### API Endpoints

#### GET /api/sensors
Returns current sensor readings:
```json
{
  "sht45": {
    "temperature": 23.45,
    "humidity": 58.2,
    "status": "ok",
    "last_read": "2025-07-24T18:30:00Z"
  },
  "hdc3022": {
    "temperature": 23.41,
    "humidity": 58.7,
    "status": "ok", 
    "last_read": "2025-07-24T18:30:00Z"
  },
  "system": {
    "uptime": 12345,
    "free_heap": 234567,
    "wifi_rssi": -45,
    "timestamp": "2025-07-24T18:30:00Z"
  }
}
```

#### GET /api/status
Returns system status:
```json
{
  "system": {
    "version": "1.0.0",
    "uptime": 12345,
    "free_heap": 234567,
    "wifi_connected": true,
    "wifi_rssi": -45,
    "ip_address": "192.168.1.180"
  },
  "sensors": {
    "sht45": {
      "connected": true,
      "last_successful_read": "2025-07-24T18:30:00Z",
      "error_count": 0
    },
    "hdc3022": {
      "connected": true,
      "last_successful_read": "2025-07-24T18:30:00Z", 
      "error_count": 0
    }
  }
}
```

#### GET /api/config
Returns current configuration:
```json
{
  "wifi": {
    "ssid": "greenhouse_network",
    "connected": true
  },
  "sensors": {
    "read_interval": 1000,
    "retry_count": 3,
    "timeout_ms": 5000
  },
  "server": {
    "port": 80,
    "cors_enabled": true
  }
}
```

#### POST /api/config
Update configuration (for future use):
```json
{
  "sensors": {
    "read_interval": 2000
  }
}
```

### Status LED Indicators
- **Solid Blue**: WiFi connected, sensors OK
- **Blinking Blue**: WiFi connecting
- **Solid Green**: Sensors reading successfully
- **Blinking Red**: Sensor error
- **Solid Red**: WiFi connection failed

## File Structure
```
feather-s3d-firmware/
├── README.md                 # This file
├── platformio.ini           # PlatformIO configuration
├── src/
│   ├── main.cpp             # Main application entry point
│   ├── sensor_manager.h     # Sensor management header
│   ├── sensor_manager.cpp   # Sensor reading and management
│   ├── web_server.h         # HTTP server header
│   ├── web_server.cpp       # HTTP API implementation
│   ├── wifi_manager.h       # WiFi management header
│   ├── wifi_manager.cpp     # WiFi connection handling
│   └── config.h             # Configuration constants
├── lib/                     # External libraries
└── test/                    # Unit tests
```

## Dependencies
- **Arduino Framework**: ESP32 Arduino Core
- **WiFi**: ESP32 WiFi library
- **WebServer**: ESP32WebServer library
- **ArduinoJson**: JSON serialization/deserialization
- **SHT4x Library**: Adafruit SHT4X sensor library
- **HDC302x Library**: Adafruit HDC302x sensor library
- **Wire**: I2C communication library

## Configuration

### WiFi Configuration
WiFi credentials can be configured via:
1. **Hard-coded**: In `config.h` (development only)
2. **WiFiManager**: Captive portal for setup (recommended)
3. **Serial Configuration**: Via serial commands (debugging)

### Network Settings
- **Default IP**: DHCP assigned
- **HTTP Port**: 80 (configurable)
- **mDNS**: `feather-sensors.local` (optional)

## Installation

### Prerequisites
- **PlatformIO**: Install PlatformIO IDE or CLI
- **ESP32 Support**: ESP32 platform and framework
- **Libraries**: Will be automatically installed via platformio.ini

### Build and Upload
```bash
# Clone the repository
cd feather-s3d-firmware

# Build the firmware
pio run

# Upload to device
pio run --target upload

# Monitor serial output
pio device monitor
```

### OTA Updates (Future)
- **Web Interface**: Upload firmware via web browser
- **HTTP API**: Programmatic firmware updates
- **Automatic Updates**: Check for updates on startup

## Testing

### Hardware Testing
1. **I2C Scanner**: Verify sensor addresses and connectivity
2. **Individual Sensors**: Test each sensor independently
3. **Concurrent Reading**: Test both sensors simultaneously
4. **Error Conditions**: Test with sensors disconnected

### Software Testing
1. **Unit Tests**: Individual function testing
2. **Integration Tests**: Full system testing
3. **Load Testing**: Continuous operation testing
4. **Network Testing**: WiFi reliability and reconnection

### Validation Testing
1. **Accuracy Testing**: Compare with reference sensors
2. **Precision Testing**: Repeated measurements analysis
3. **Environmental Testing**: Various temperature/humidity conditions
4. **Long-term Testing**: 24+ hour continuous operation

## Troubleshooting

### Common Issues
1. **Sensor Not Detected**: Check I2C connections and addresses
2. **WiFi Connection Failed**: Verify credentials and signal strength
3. **HTTP Timeouts**: Check network connectivity and server load
4. **Memory Issues**: Monitor heap usage and optimize if needed

### Debug Features
- **Serial Logging**: Detailed debug output via serial port
- **Status LED**: Visual indication of system state
- **HTTP Status**: Real-time status via API endpoints
- **Error Counters**: Track and report error frequencies

## Performance Specifications

### Sensor Reading Performance
- **Update Rate**: 1 Hz (configurable)
- **Response Time**: <100ms per sensor
- **Accuracy**: ±0.1°C temperature, ±1-2% RH humidity
- **Stability**: <0.02°C/hour drift

### Network Performance
- **HTTP Response**: <50ms typical
- **Concurrent Requests**: Up to 4 simultaneous
- **WiFi Reconnection**: <10 seconds typical
- **Uptime Target**: >99.9%

### Power Consumption
- **Active Mode**: ~80mA @ 3.3V
- **WiFi Transmit**: ~120mA peak
- **Sleep Mode**: <1mA (future feature)
- **Power Supply**: USB or 3.7V LiPo battery

---

*This firmware is designed for the greenhouse monitoring precision sensors upgrade project.*