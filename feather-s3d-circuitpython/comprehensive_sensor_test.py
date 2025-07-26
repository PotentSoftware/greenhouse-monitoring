"""
Comprehensive Feather S3[D] Sensor Test
Identify all connected sensors and get readings
"""

import time
import board
import busio

print("🌱 Comprehensive Sensor Test")
print("=" * 40)

# Import libraries
try:
    import adafruit_sht4x
    sht4x_available = True
    print("✅ SHT4x library imported")
except ImportError:
    sht4x_available = False
    print("❌ SHT4x library not available")

try:
    import adafruit_hdc302x
    hdc302x_available = True
    print("✅ HDC302x library imported")
except ImportError:
    hdc302x_available = False
    print("❌ HDC302x library not available")

# Create I2C buses
i2c1 = busio.I2C(board.SCL, board.SDA)
i2c2 = board.I2C2()

print("\n🔍 Scanning I2C buses...")

# Scan I2C1
while not i2c1.try_lock():
    pass
i2c1_devices = i2c1.scan()
i2c1.unlock()
print(f"I2C1 devices: {[hex(d) for d in i2c1_devices]}")

# Scan I2C2  
while not i2c2.try_lock():
    pass
i2c2_devices = i2c2.scan()
i2c2.unlock()
print(f"I2C2 devices: {[hex(d) for d in i2c2_devices]}")

# Test each device on each bus
print("\n🔧 Testing sensors...")

def test_sht4x(i2c_bus, bus_name, address):
    if not sht4x_available or address not in (i2c1_devices if bus_name == "I2C1" else i2c2_devices):
        return None
    
    try:
        sensor = adafruit_sht4x.SHT4x(i2c_bus)
        temp = sensor.temperature
        humidity = sensor.relative_humidity
        print(f"✅ SHT4x on {bus_name}: {temp:.1f}°C, {humidity:.1f}%RH")
        return {"type": "SHT4x", "temperature": temp, "humidity": humidity}
    except Exception as e:
        print(f"❌ SHT4x failed on {bus_name}: {e}")
        return None

def test_hdc302x(i2c_bus, bus_name, address):
    if not hdc302x_available or address not in (i2c1_devices if bus_name == "I2C1" else i2c2_devices):
        return None
    
    try:
        sensor = adafruit_hdc302x.HDC302x(i2c_bus)
        temp = sensor.temperature
        humidity = sensor.relative_humidity
        print(f"✅ HDC302x on {bus_name}: {temp:.1f}°C, {humidity:.1f}%RH")
        return {"type": "HDC302x", "temperature": temp, "humidity": humidity}
    except Exception as e:
        print(f"❌ HDC302x failed on {bus_name}: {e}")
        return None

# Test common sensor addresses
sensor_results = {}

# Test 0x44 (common SHT address)
if 0x44 in i2c1_devices:
    print(f"\n🎯 Testing 0x44 on I2C1...")
    result = test_sht4x(i2c1, "I2C1", 0x44)
    if result:
        sensor_results["I2C1_0x44"] = result
    else:
        result = test_hdc302x(i2c1, "I2C1", 0x44)
        if result:
            sensor_results["I2C1_0x44"] = result

if 0x44 in i2c2_devices:
    print(f"\n🎯 Testing 0x44 on I2C2...")
    result = test_sht4x(i2c2, "I2C2", 0x44)
    if result:
        sensor_results["I2C2_0x44"] = result
    else:
        result = test_hdc302x(i2c2, "I2C2", 0x44)
        if result:
            sensor_results["I2C2_0x44"] = result

# Test 0x36 (unknown device)
if 0x36 in i2c1_devices:
    print(f"\n🎯 Testing 0x36 on I2C1...")
    # Try both sensor types
    result = test_sht4x(i2c1, "I2C1", 0x36)
    if result:
        sensor_results["I2C1_0x36"] = result
    else:
        result = test_hdc302x(i2c1, "I2C1", 0x36)
        if result:
            sensor_results["I2C1_0x36"] = result
        else:
            print("❓ Device at 0x36 is not SHT4x or HDC302x")

# Test other common HDC addresses
hdc_addresses = [0x40, 0x41, 0x42, 0x43]
for addr in hdc_addresses:
    if addr in i2c1_devices:
        print(f"\n🎯 Testing HDC302x at 0x{addr:02x} on I2C1...")
        result = test_hdc302x(i2c1, "I2C1", addr)
        if result:
            sensor_results[f"I2C1_0x{addr:02x}"] = result
    
    if addr in i2c2_devices:
        print(f"\n🎯 Testing HDC302x at 0x{addr:02x} on I2C2...")
        result = test_hdc302x(i2c2, "I2C2", addr)
        if result:
            sensor_results[f"I2C2_0x{addr:02x}"] = result

# Summary
print(f"\n📋 FINAL RESULTS:")
print(f"=" * 30)
print(f"Total working sensors: {len(sensor_results)}")

if sensor_results:
    for location, data in sensor_results.items():
        print(f"✅ {location}: {data['type']} - {data['temperature']:.1f}°C, {data['humidity']:.1f}%RH")
else:
    print("❌ No working sensors found")

print(f"\nRaw I2C devices:")
print(f"  I2C1: {[hex(d) for d in i2c1_devices]}")
print(f"  I2C2: {[hex(d) for d in i2c2_devices]}")

# Continuous reading loop
if sensor_results:
    print(f"\n🔄 Starting continuous reading (5 readings)...")
    for i in range(5):
        print(f"\n--- Reading {i+1}/5 ---")
        for location, _ in sensor_results.items():
            bus_name, addr_str = location.split("_")
            addr = int(addr_str, 16)
            
            if bus_name == "I2C1":
                if addr == 0x44:
                    try:
                        sensor = adafruit_sht4x.SHT4x(i2c1)
                        print(f"{location}: {sensor.temperature:.1f}°C, {sensor.relative_humidity:.1f}%RH")
                    except:
                        print(f"{location}: Read error")
            elif bus_name == "I2C2":
                if addr == 0x44:
                    try:
                        sensor = adafruit_sht4x.SHT4x(i2c2)
                        print(f"{location}: {sensor.temperature:.1f}°C, {sensor.relative_humidity:.1f}%RH")
                    except:
                        print(f"{location}: Read error")
        
        time.sleep(2)

print("\n✅ Comprehensive test complete!")

# Cleanup
i2c1.deinit()
i2c2.deinit()
