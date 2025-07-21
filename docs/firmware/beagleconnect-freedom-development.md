# BeagleConnect Freedom Firmware Development Guide

## Overview

The BeagleConnect Freedom firmware is a custom Zephyr-based implementation that provides Greybus protocol support for greenhouse monitoring sensors. This firmware enables wireless communication between the BeagleConnect Freedom device and the BeaglePlay via IEEE 802.15.4 and 6LoWPAN.

## Architecture

### Hardware Components
- **BeagleConnect Freedom**: CC1352P7 microcontroller with IEEE 802.15.4 radio
- **Sensors**: 
  - OPT3001 light sensor (I2C address 0x44)
  - HDC2010 temperature/humidity sensor (I2C address 0x41)
  - pH sensor (analog input)

### Software Stack
```
┌─────────────────────────────────────┐
│         Greenhouse Application      │
├─────────────────────────────────────┤
│            Greybus Protocol         │
├─────────────────────────────────────┤
│         I2C Protocol Handler        │
├─────────────────────────────────────┤
│           Sensor Drivers            │
├─────────────────────────────────────┤
│         Zephyr RTOS Kernel          │
├─────────────────────────────────────┤
│           CC1352P7 Hardware         │
└─────────────────────────────────────┘
```

## Custom Modifications

### 1. I2C Protocol Implementation
- **File**: `src/i2c.c`, `include/i2c.h`
- **Purpose**: Implements Greybus I2C protocol for sensor communication
- **Features**:
  - OPT3001 light sensor support
  - HDC2010 temperature/humidity sensor support
  - Error handling and logging
  - Simulated data fallback for development

### 2. Enhanced SVC Protocol
- **File**: `src/svc.c`
- **Purpose**: Service (SVC) protocol handlers for Greybus enumeration
- **Features**:
  - V_SYS power management
  - RefClk configuration
  - UniPro interface management
  - Interface activation

### 3. Greybus Manifest
- **File**: `src/local_node.c`
- **Purpose**: Defines device capabilities and interfaces
- **Features**:
  - I2C bundle descriptor (class 0x0a, protocol 0x03)
  - Vendor/product identification
  - CPort routing configuration

### 4. Configuration
- **File**: `prj.conf`
- **Purpose**: Zephyr project configuration
- **Key Settings**:
  - I2C subsystem enabled
  - IEEE 802.15.4 networking
  - Greybus protocol support
  - Debug logging configuration

## Development Environment Setup

### Prerequisites
1. **Zephyr SDK**: Version 0.16.3 or later
2. **Python**: 3.8+ with virtual environment
3. **West**: Zephyr build tool
4. **CC1352 Flasher**: For firmware deployment

### Initial Setup
```bash
# Navigate to project root
cd /path/to/greenhouse-monitoring

# Initialize submodules (if not already done)
git submodule update --init --recursive

# Set up Zephyr environment
python3 -m venv .venv
source .venv/bin/activate
pip install west

# Initialize west workspace
west init -l firmware/beagleconnect-freedom
west update

# Install Zephyr SDK (if not already installed)
cd ~
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.3/zephyr-sdk-0.16.3_linux-x86_64.tar.xz
tar xf zephyr-sdk-0.16.3_linux-x86_64.tar.xz
cd zephyr-sdk-0.16.3
./setup.sh
```

### Environment Variables
```bash
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR=~/zephyr-sdk-0.16.3
```

## Building and Flashing

### Using the Build Script
```bash
# From project root
./firmware/tools/build-and-flash.sh
```

### Manual Build Process
```bash
# Navigate to firmware directory
cd firmware/beagleconnect-freedom

# Build firmware
west build -b beagleconnect_freedom

# Flash to device (requires USB connection)
python ~/cc1352-flasher/src/cc1352_flasher/cli.py --bcf -e -w -v build/zephyr/zephyr.bin
```

## Testing and Debugging

### USB Connection Testing
```bash
# Check device connection
lsusb | grep -i beagle

# Monitor serial output
screen /dev/ttyACM0 115200
```

### Wireless Connection Testing
```bash
# On BeaglePlay, check for device enumeration
ls -la /sys/bus/greybus/devices/

# Check IIO devices
ls -la /sys/bus/iio/devices/

# Test sensor data
cat /sys/bus/iio/devices/iio:device*/in_*_raw
```

### Debug Logging
The firmware includes comprehensive debug logging:
- **SVC Protocol**: Service enumeration and configuration
- **I2C Protocol**: Sensor communication and data transfer
- **Greybus Messages**: Protocol message handling
- **HDLC Frames**: Low-level communication debugging

## Integration with Greenhouse System

### Data Flow
1. **Sensor Reading**: Firmware reads OPT3001 and HDC2010 sensors via I2C
2. **Greybus Protocol**: Data transmitted via Greybus I2C protocol
3. **IIO Framework**: BeaglePlay creates IIO devices for sensors
4. **Python Application**: Greenhouse monitoring reads IIO devices
5. **Web Dashboard**: Real-time display of sensor data

### API Integration
The firmware provides sensor data that appears as IIO devices on BeaglePlay:
- `iio:device1` - OPT3001 light sensor
- `iio:device2` - HDC2010 temperature/humidity sensor

### Configuration Files
- **Device Tree**: Hardware configuration in Zephyr device tree format
- **Kconfig**: Build-time configuration options
- **prj.conf**: Project-specific configuration

## Troubleshooting

### Common Issues

#### 1. Build Failures
- **Symptom**: West build fails with missing dependencies
- **Solution**: Ensure Zephyr SDK is properly installed and environment variables are set

#### 2. Flash Failures
- **Symptom**: CC1352 flasher cannot connect to device
- **Solution**: Check USB connection, ensure device is in bootloader mode

#### 3. Greybus Enumeration Issues
- **Symptom**: No IIO devices appear on BeaglePlay
- **Solution**: Check wireless connectivity, verify gbridge service is running

#### 4. Sensor Communication Issues
- **Symptom**: Sensor readings are zero or invalid
- **Solution**: Verify I2C wiring, check sensor power supply

### Debug Commands
```bash
# Check Greybus devices
ssh debian@beagleplay "ls -la /sys/bus/greybus/devices/"

# Monitor gbridge logs
ssh debian@beagleplay "journalctl -u beagleconnect-gateway.service -f"

# Check network interface
ssh debian@beagleplay "ip -6 addr show lowpan0"

# Test wireless connectivity
ssh debian@beagleplay "ping6 -c 3 2001:db8::1"
```

## Version Control

### Submodule Management
```bash
# Update firmware to latest version
git submodule update --remote firmware/beagleconnect-freedom

# Commit submodule changes
git add firmware/beagleconnect-freedom
git commit -m "Update BeagleConnect Freedom firmware to latest version"

# Push changes
git push origin main
```

### Custom Changes
All custom modifications are committed to the firmware repository and tracked via the submodule. This ensures:
- Version correlation between firmware and application
- Reproducible builds
- Easy rollback to previous versions
- Clear change history

## Future Enhancements

### Planned Features
1. **Power Management**: Sleep modes for battery operation
2. **OTA Updates**: Over-the-air firmware updates
3. **Additional Sensors**: Support for more I2C sensors
4. **Mesh Networking**: Multi-device communication
5. **Security**: Encrypted communication

### Development Workflow
1. Make changes in `firmware/beagleconnect-freedom/`
2. Test with build and flash script
3. Verify integration with greenhouse system
4. Commit changes to firmware repository
5. Update submodule reference in main project
6. Document changes and update version

## References

- [Zephyr Project Documentation](https://docs.zephyrproject.org/)
- [Greybus Protocol Specification](https://github.com/projectara/greybus-spec)
- [BeagleConnect Freedom Hardware](https://beagleboard.org/beagleconnect-freedom)
- [CC1352P7 Datasheet](https://www.ti.com/product/CC1352P7)
- [OPT3001 Sensor Documentation](https://www.ti.com/product/OPT3001)
- [HDC2010 Sensor Documentation](https://www.ti.com/product/HDC2010)
