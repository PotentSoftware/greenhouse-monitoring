"""
Feather S3[D] Dual Sensor Reading Test
Test both SHT45 and HDC3022 sensors on STEMMA QT connectors
"""

import time
import board
import busio
import json

print("🌱 Feather S3[D] Dual Sensor Reading Test")
print("=" * 50)

print(f"📋 Board ID: {board.board_id}")

# Import sensor libraries
try:
    import adafruit_sht4x
    print("✅ SHT4x library imported")
except ImportError as e:
    print(f"❌ SHT4x library failed: {e}")
    adafruit_sht4x = None

try:
    import adafruit_hdc302x
    print("✅ HDC302x library imported")
except ImportError as e:
    print(f"❌ HDC302x library failed: {e}")
    adafruit_hdc302x = None

# Create I2C buses
print("\n🔧 Creating I2C buses...")

# Default I2C bus
try:
    i2c1 = busio.I2C(board.SCL, board.SDA)
    print("✅ I2C1 (default) created")
except Exception as e:
    print(f"❌ I2C1 failed: {e}")
    i2c1 = None

# Second I2C bus
try:
    i2c2 = board.I2C2()
    print("✅ I2C2 created")
except Exception as e:
    print(f"❌ I2C2 failed: {e}")
    i2c2 = None

# Scan both buses
def scan_i2c_bus(i2c_bus, bus_name):
    if not i2c_bus:
        return []
    
    try:
        while not i2c_bus.try_lock():
            pass
        devices = i2c_bus.scan()
        i2c_bus.unlock()
        
        print(f"🔍 {bus_name} devices: {[hex(d) for d in devices]}")
        return devices
    except Exception as e:
        print(f"❌ {bus_name} scan failed: {e}")
        return []

print("\n🔍 Scanning I2C buses...")
i2c1_devices = scan_i2c_bus(i2c1, "I2C1")
i2c2_devices = scan_i2c_bus(i2c2, "I2C2")

# Try to initialize sensors on both buses
sensors = {}

def try_sensor_init(i2c_bus, bus_name, sensor_lib, sensor_name, expected_addr):
    if not i2c_bus or not sensor_lib:
        return None
    
    try:
        if expected_addr in (i2c1_devices if bus_name == "I2C1" else i2c2_devices):
            sensor = sensor_lib.SHT4x(i2c_bus) if "SHT" in sensor_name else sensor_lib.HDC302x(i2c_bus)
            print(f"✅ {sensor_name} initialized on {bus_name}")
            return sensor
        else:
            print(f"❌ {sensor_name} not found at 0x{expected_addr:02x} on {bus_name}")
            return None
    except Exception as e:
        print(f"❌ {sensor_name} init failed on {bus_name}: {e}")
        return None

print("\n🔧 Initializing sensors...")

# Try SHT45 on both buses (expected at 0x44)
sht45_i2c1 = try_sensor_init(i2c1, "I2C1", adafruit_sht4x, "SHT45", 0x44)
sht45_i2c2 = try_sensor_init(i2c2, "I2C2", adafruit_sht4x, "SHT45", 0x44)

# Try HDC3022 on both buses (expected at 0x41)
hdc3022_i2c1 = try_sensor_init(i2c1, "I2C1", adafruit_hdc302x, "HDC3022", 0x41)
hdc3022_i2c2 = try_sensor_init(i2c2, "I2C2", adafruit_hdc302x, "HDC3022", 0x41)

# Also try HDC3022 at other common addresses
for addr in [0x40, 0x42, 0x43]:
    if addr in i2c1_devices:
        try:
            hdc_test = adafruit_hdc302x.HDC302x(i2c1)
            print(f"✅ HDC3022 found at 0x{addr:02x} on I2C1")
            if not hdc3022_i2c1:
                hdc3022_i2c1 = hdc_test
            break
        except:
            pass
    
    if addr in i2c2_devices:
        try:
            hdc_test = adafruit_hdc302x.HDC302x(i2c2)
            print(f"✅ HDC3022 found at 0x{addr:02x} on I2C2")
            if not hdc3022_i2c2:
                hdc3022_i2c2 = hdc_test
            break
        except:
            pass

# Test sensor readings
print("\n📊 Testing sensor readings...")

def read_sensor(sensor, sensor_name):
    if not sensor:
        return None
    
    try:
        if "SHT" in sensor_name:
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
        else:  # HDC
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
        
        print(f"✅ {sensor_name}: {temperature:.1f}°C, {humidity:.1f}%RH")
        return {"temperature": temperature, "humidity": humidity}
    except Exception as e:
        print(f"❌ {sensor_name} reading failed: {e}")
        return None

# Read from all available sensors
readings = {}

if sht45_i2c1:
    readings["SHT45_I2C1"] = read_sensor(sht45_i2c1, "SHT45_I2C1")

if sht45_i2c2:
    readings["SHT45_I2C2"] = read_sensor(sht45_i2c2, "SHT45_I2C2")

if hdc3022_i2c1:
    readings["HDC3022_I2C1"] = read_sensor(hdc3022_i2c1, "HDC3022_I2C1")

if hdc3022_i2c2:
    readings["HDC3022_I2C2"] = read_sensor(hdc3022_i2c2, "HDC3022_I2C2")

# Summary
print(f"\n📋 Summary:")
print(f"   Total sensors found: {len([r for r in readings.values() if r])}")
print(f"   I2C1 devices: {len(i2c1_devices)}")
print(f"   I2C2 devices: {len(i2c2_devices)}")

if readings:
    print("\n🎯 Sensor readings:")
    for sensor_name, data in readings.items():
        if data:
            print(f"   {sensor_name}: {data['temperature']:.1f}°C, {data['humidity']:.1f}%RH")

print("\n✅ Sensor test complete!")
print("🔄 Continuous reading will start next...")
