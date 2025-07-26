"""
Feather S3[D] Dual Precision Sensors - CircuitPython Implementation
Temperature and Humidity monitoring with SHT45 + HDC3022

Hardware Configuration:
- SHT45 sensor on I2C1 (SCL1/SDA1 pins) - ±0.1°C, ±1% RH accuracy
- HDC3022 sensor on I2C2 (SCL2/SDA2 pins) - ±0.1°C, ±2% RH accuracy
- USB serial output for development and testing
- Future: HTTP server for BeaglePlay integration

Connection:
- SHT45: Connect to I2C1 (STEMMA QT connector or SCL1/SDA1 pins)
- HDC3022: Connect to I2C2 (STEMMA QT connector or SCL2/SDA2 pins)
"""

import time
import board
import busio
import digitalio
import json
from adafruit_sht4x import SHT4x
from adafruit_hdc302x import HDC302x

# Status LED setup
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# I2C bus setup for dual sensors
print("🌱 Feather S3[D] Precision Sensors Starting...")
print("🔧 Initializing I2C buses...")

# I2C1 for SHT45 sensor
try:
    print(f"🔧 Attempting I2C1 on pins SCL1={board.SCL1}, SDA1={board.SDA1}")
    i2c1 = busio.I2C(board.SCL1, board.SDA1)
    print("✅ I2C1 bus initialized (for SHT45)")
    i2c1_available = True
except Exception as e:
    print(f"❌ I2C1 bus failed: {e}")
    i2c1_available = False

# I2C2 for HDC3022 sensor  
try:
    print(f"🔧 Attempting I2C2 on pins SCL2={board.SCL2}, SDA2={board.SDA2}")
    i2c2 = busio.I2C(board.SCL2, board.SDA2)
    print("✅ I2C2 bus initialized (for HDC3022)")
    i2c2_available = True
except Exception as e:
    print(f"❌ I2C2 bus failed: {e}")
    i2c2_available = False

# Sensor initialization
sht45_sensor = None
hdc3022_sensor = None
sht45_available = False
hdc3022_available = False

# Initialize SHT45 sensor on I2C1
if i2c1_available:
    try:
        sht45_sensor = SHT4x(i2c1)
        print("✅ SHT45 sensor initialized on I2C1")
        print(f"   SHT45 Serial Number: 0x{sht45_sensor.serial_number:08X}")
        sht45_available = True
    except Exception as e:
        print(f"❌ SHT45 sensor failed: {e}")
        print("   Check SHT45 wiring to I2C1 (SCL1/SDA1)")

# Initialize HDC3022 sensor on I2C2
if i2c2_available:
    try:
        hdc3022_sensor = HDC302x(i2c2)
        print("✅ HDC3022 sensor initialized on I2C2")
        print(f"   HDC3022 Device ID: 0x{hdc3022_sensor.device_id:04X}")
        hdc3022_available = True
    except Exception as e:
        print(f"❌ HDC3022 sensor failed: {e}")
        print("   Check HDC3022 wiring to I2C2 (SCL2/SDA2)")

# Sensor reading functions
def read_sht45():
    """Read temperature and humidity from SHT45 sensor"""
    if not sht45_available:
        return None, None, "disconnected"
    
    try:
        temperature = sht45_sensor.temperature
        humidity = sht45_sensor.relative_humidity
        return temperature, humidity, "connected"
    except Exception as e:
        print(f"❌ SHT45 read error: {e}")
        return None, None, "error"

def read_hdc3022():
    """Read temperature and humidity from HDC3022 sensor"""
    if not hdc3022_available:
        return None, None, "disconnected"
    
    try:
        temperature = hdc3022_sensor.temperature
        humidity = hdc3022_sensor.relative_humidity
        return temperature, humidity, "connected"
    except Exception as e:
        print(f"❌ HDC3022 read error: {e}")
        return None, None, "error"

def calculate_averages(sht45_temp, sht45_hum, sht45_status, hdc3022_temp, hdc3022_hum, hdc3022_status):
    """Calculate averaged temperature and humidity from available sensors"""
    temp_readings = []
    humidity_readings = []
    
    # Collect valid temperature readings
    if sht45_status == "connected" and sht45_temp is not None:
        temp_readings.append(sht45_temp)
    if hdc3022_status == "connected" and hdc3022_temp is not None:
        temp_readings.append(hdc3022_temp)
    
    # Collect valid humidity readings
    if sht45_status == "connected" and sht45_hum is not None:
        humidity_readings.append(sht45_hum)
    if hdc3022_status == "connected" and hdc3022_hum is not None:
        humidity_readings.append(hdc3022_hum)
    
    # Calculate averages
    avg_temp = sum(temp_readings) / len(temp_readings) if temp_readings else None
    avg_humidity = sum(humidity_readings) / len(humidity_readings) if humidity_readings else None
    
    return avg_temp, avg_humidity, len(temp_readings), len(humidity_readings)

def calculate_vpd(temperature, humidity):
    """Calculate Vapor Pressure Deficit (VPD) in kPa"""
    if temperature is None or humidity is None:
        return None
    
    # Saturated vapor pressure using Magnus formula
    svp = 0.6108 * (2.71828 ** (17.27 * temperature / (temperature + 237.3)))
    
    # VPD calculation
    vpd = (1 - humidity / 100) * svp
    return vpd

def format_sensor_data():
    """Format all sensor data as JSON for output"""
    # Read individual sensors
    sht45_temp, sht45_hum, sht45_status = read_sht45()
    hdc3022_temp, hdc3022_hum, hdc3022_status = read_hdc3022()
    
    # Calculate averages
    avg_temp, avg_humidity, temp_count, humidity_count = calculate_averages(
        sht45_temp, sht45_hum, sht45_status,
        hdc3022_temp, hdc3022_hum, hdc3022_status
    )
    
    # Calculate VPD using averaged values
    vpd = calculate_vpd(avg_temp, avg_humidity)
    
    # Format data structure
    data = {
        "timestamp": time.monotonic(),
        "sht45": {
            "temperature": round(sht45_temp, 2) if sht45_temp is not None else None,
            "humidity": round(sht45_hum, 1) if sht45_hum is not None else None,
            "status": sht45_status
        },
        "hdc3022": {
            "temperature": round(hdc3022_temp, 2) if hdc3022_temp is not None else None,
            "humidity": round(hdc3022_hum, 1) if hdc3022_hum is not None else None,
            "status": hdc3022_status
        },
        "averaged": {
            "temperature": round(avg_temp, 2) if avg_temp is not None else None,
            "humidity": round(avg_humidity, 1) if avg_humidity is not None else None,
            "temp_sensor_count": temp_count,
            "humidity_sensor_count": humidity_count
        },
        "vpd": round(vpd, 3) if vpd is not None else None,
        "system": {
            "i2c1_available": i2c1_available,
            "i2c2_available": i2c2_available,
            "sht45_available": sht45_available,
            "hdc3022_available": hdc3022_available
        }
    }
    
    return data

def print_sensor_summary(data):
    """Print human-readable sensor summary"""
    print("\n" + "="*60)
    print("🌡️  PRECISION SENSORS READING")
    print("="*60)
    
    # Individual sensors
    print(f"🔬 SHT45 (±0.1°C, ±1% RH):  {data['sht45']['temperature']}°C / {data['sht45']['humidity']}% [{data['sht45']['status']}]")
    print(f"🔬 HDC3022 (±0.1°C, ±2% RH): {data['hdc3022']['temperature']}°C / {data['hdc3022']['humidity']}% [{data['hdc3022']['status']}]")
    
    # Averaged values
    if data['averaged']['temperature'] is not None:
        print(f"📊 AVERAGED ({data['averaged']['temp_sensor_count']} sensors): {data['averaged']['temperature']}°C / {data['averaged']['humidity']}%")
    else:
        print("📊 AVERAGED: No sensor data available")
    
    # VPD
    if data['vpd'] is not None:
        vpd_status = "OPTIMAL" if 0.8 <= data['vpd'] <= 1.2 else "CHECK"
        print(f"💧 VPD: {data['vpd']} kPa [{vpd_status}]")
    else:
        print("💧 VPD: Cannot calculate (no sensor data)")
    
    print("="*60)

# Main execution
print("\n🚀 Starting sensor monitoring loop...")
print("📊 Data will be displayed every 5 seconds")
print("🔌 USB Serial connection active for development")

if not sht45_available and not hdc3022_available:
    print("\n❌ ERROR: No sensors detected!")
    print("🔧 Please check sensor connections:")
    print("   - SHT45 should be connected to I2C1 (SCL1/SDA1)")
    print("   - HDC3022 should be connected to I2C2 (SCL2/SDA2)")
    print("   - Ensure STEMMA QT cables are properly connected")
    print("   - Check sensor power (3.3V)")

# Main monitoring loop
loop_count = 0
while True:
    try:
        # Flash LED to show activity
        led.value = True
        
        # Read and format sensor data
        sensor_data = format_sensor_data()
        
        # Print summary every reading
        print_sensor_summary(sensor_data)
        
        # Print JSON data every 10th reading for debugging
        if loop_count % 10 == 0:
            print("\n📋 JSON Data (for HTTP server integration):")
            print(json.dumps(sensor_data))
        
        # Turn off LED
        led.value = False
        
        # Wait before next reading
        time.sleep(5)
        loop_count += 1
        
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        break
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        led.value = False
        time.sleep(5)

print("👋 Sensor monitoring ended")
