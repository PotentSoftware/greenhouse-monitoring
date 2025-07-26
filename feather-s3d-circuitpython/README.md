# Feather S3[D] Precision Sensors Setup Guide

## 🎯 Objective
Get dual temperature and humidity measurements from SHT45 and HDC3022 sensors using CircuitPython on the Feather S3[D].

## 🔧 Hardware Setup

### Required Components
- **Feather S3[D]** (CircuitPython pre-installed)
- **SHT45 sensor** (±0.1°C, ±1% RH accuracy)
- **HDC3022 sensor** (±0.1°C, ±2% RH accuracy)
- **STEMMA QT cables** or jumper wires
- **USB cable** for power and data

### Sensor Connections

#### SHT45 → I2C1 (Primary sensor)
```
SHT45    Feather S3[D]
VCC   →  3.3V
GND   →  GND
SCL   →  SCL1 (GPIO9)
SDA   →  SDA1 (GPIO8)
```

#### HDC3022 → I2C2 (Secondary sensor)
```
HDC3022  Feather S3[D]
VCC   →  3.3V
GND   →  GND
SCL   →  SCL2 (GPIO18)
SDA   →  SDA2 (GPIO17)
```

### STEMMA QT Connection (Recommended)
If your sensors have STEMMA QT connectors:
1. Connect SHT45 to the first STEMMA QT port (I2C1)
2. Connect HDC3022 to the second STEMMA QT port (I2C2)
3. Use STEMMA QT cables for clean, reliable connections

## 💾 Software Setup

### Step 1: Install Required Libraries
1. Download the CircuitPython Library Bundle:
   - Visit: https://circuitpython.org/libraries
   - Download the latest bundle for your CircuitPython version

2. Extract and copy these libraries to `CIRCUITPY/lib/`:
   ```
   adafruit_sht4x.mpy
   adafruit_hdc302x.mpy
   adafruit_bus_device/ (entire folder)
   adafruit_register/ (entire folder)
   ```

### Step 2: Deploy Code
1. Copy `code.py` to the root of the CIRCUITPY drive
2. The board will automatically restart and begin running

### Step 3: Monitor Output
1. Open a serial terminal (115200 baud):
   - **Windows**: PuTTY, Tera Term, or Arduino IDE Serial Monitor
   - **macOS/Linux**: `screen /dev/ttyACM0 115200` or `cu -l /dev/ttyACM0 -s 115200`
   - **Any OS**: Mu Editor, Thonny, or VS Code with CircuitPython extension

## 📊 Expected Output

### Successful Operation
```
🌱 Feather S3[D] Precision Sensors Starting...
🔧 Initializing I2C buses...
✅ I2C1 bus initialized (for SHT45)
✅ I2C2 bus initialized (for HDC3022)
✅ SHT45 sensor initialized on I2C1
   SHT45 Serial Number: 0x12345678
✅ HDC3022 sensor initialized on I2C2
   HDC3022 Device ID: 0x5449

🚀 Starting sensor monitoring loop...
📊 Data will be displayed every 5 seconds

============================================================
🌡️  PRECISION SENSORS READING
============================================================
🔬 SHT45 (±0.1°C, ±1% RH):  22.45°C / 58.2% [connected]
🔬 HDC3022 (±0.1°C, ±2% RH): 22.38°C / 58.8% [connected]
📊 AVERAGED (2 sensors): 22.42°C / 58.5%
💧 VPD: 1.125 kPa [OPTIMAL]
============================================================
```

### Troubleshooting Common Issues

#### No Sensors Detected
```
❌ ERROR: No sensors detected!
🔧 Please check sensor connections:
   - SHT45 should be connected to I2C1 (SCL1/SDA1)
   - HDC3022 should be connected to I2C2 (SCL2/SDA2)
```

**Solutions:**
1. **Check power**: Ensure sensors are getting 3.3V
2. **Check wiring**: Verify SCL/SDA connections
3. **Check I2C addresses**: SHT45 (0x44), HDC3022 (0x41)
4. **Try one sensor**: Test each sensor individually
5. **Check libraries**: Ensure all required libraries are installed

#### Only One Sensor Working
- Check connections for the non-working sensor
- Verify the sensor is compatible (SHT45/HDC3022)
- Try swapping sensor positions to isolate the issue

#### Library Import Errors
```
ImportError: no module named 'adafruit_sht4x'
```
- Download and install the missing library
- Ensure the library version matches your CircuitPython version
- Check that the library file is in `CIRCUITPY/lib/`

## 🔍 Data Format

The sensors output data in this JSON format:
```json
{
  "timestamp": 12345.67,
  "sht45": {
    "temperature": 22.45,
    "humidity": 58.2,
    "status": "connected"
  },
  "hdc3022": {
    "temperature": 22.38,
    "humidity": 58.8,
    "status": "connected"
  },
  "averaged": {
    "temperature": 22.42,
    "humidity": 58.5,
    "temp_sensor_count": 2,
    "humidity_sensor_count": 2
  },
  "vpd": 1.125,
  "system": {
    "i2c1_available": true,
    "i2c2_available": true,
    "sht45_available": true,
    "hdc3022_available": true
  }
}
```

## 📈 Sensor Specifications

### SHT45 (Primary)
- **Temperature Accuracy**: ±0.1°C (typical)
- **Humidity Accuracy**: ±1% RH (typical)
- **I2C Address**: 0x44
- **Response Time**: <8 seconds (63% of step change)

### HDC3022 (Secondary)
- **Temperature Accuracy**: ±0.1°C (typical)
- **Humidity Accuracy**: ±2% RH (typical)
- **I2C Address**: 0x41
- **Response Time**: <15 seconds (63% of step change)

## 🎯 VPD (Vapor Pressure Deficit) Information

**Optimal VPD Range**: 0.8 - 1.2 kPa for most plants

- **< 0.8 kPa**: Low transpiration, potential for mold/mildew
- **0.8 - 1.2 kPa**: Optimal range for most plants
- **> 1.2 kPa**: High transpiration, potential plant stress

## 🔄 Next Steps

1. **Verify sensor readings**: Ensure both sensors are providing realistic data
2. **Test accuracy**: Compare readings between sensors (should be very close)
3. **WiFi integration**: Add HTTP server for BeaglePlay communication
4. **Data logging**: Implement local data storage
5. **Error handling**: Add robust error recovery and reconnection logic

## 🆘 Support

If you encounter issues:
1. Check all connections and power
2. Verify library installations
3. Test sensors individually
4. Check CircuitPython version compatibility
5. Review serial output for specific error messages
