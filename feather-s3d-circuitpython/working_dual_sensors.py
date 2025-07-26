"""
Working Feather S3[D] Dual Sensor Implementation
Based on actual hardware detection results
"""

import time
import board
import busio
import json
import math

print("🌱 Feather S3[D] Dual Sensor System")
print("=" * 45)

# Import libraries
import adafruit_sht4x
import adafruit_hdc302x

# Create I2C buses
i2c1 = busio.I2C(board.SCL, board.SDA)  # SHT45 sensor
i2c2 = board.I2C2()                     # HDC3022 sensor (problematic)

print("✅ I2C buses created")

# Initialize sensors
sht45 = None
hdc3022 = None

# Initialize SHT45 on I2C1
try:
    sht45 = adafruit_sht4x.SHT4x(i2c1)
    print("✅ SHT45 initialized on I2C1")
except Exception as e:
    print(f"❌ SHT45 initialization failed: {e}")

# Initialize HDC3022 on I2C2 with error handling
try:
    hdc3022 = adafruit_hdc302x.HDC302x(i2c2)
    print("✅ HDC3022 initialized on I2C2")
except Exception as e:
    print(f"❌ HDC3022 initialization failed: {e}")

def read_sht45():
    """Read SHT45 sensor with error handling"""
    if not sht45:
        return None
    
    try:
        temp = sht45.temperature
        humidity = sht45.relative_humidity
        
        # Validate readings
        if -40 <= temp <= 125 and 0 <= humidity <= 100:
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "status": "ok"
            }
        else:
            return {
                "temperature": None,
                "humidity": None,
                "status": "invalid_range"
            }
    except Exception as e:
        return {
            "temperature": None,
            "humidity": None,
            "status": f"error: {e}"
        }

def read_hdc3022():
    """Read HDC3022 sensor with error handling and validation"""
    if not hdc3022:
        return None
    
    try:
        temp = hdc3022.temperature
        humidity = hdc3022.relative_humidity
        
        # Validate readings (HDC3022 was giving -45°C, 0%RH)
        if -40 <= temp <= 125 and 0 <= humidity <= 100:
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "status": "ok"
            }
        else:
            return {
                "temperature": None,
                "humidity": None,
                "status": "invalid_range"
            }
    except Exception as e:
        return {
            "temperature": None,
            "humidity": None,
            "status": f"error: {e}"
        }

def calculate_vpd(temp_c, humidity_percent):
    """Calculate Vapor Pressure Deficit"""
    if temp_c is None or humidity_percent is None:
        return None
    
    try:
        # Saturation vapor pressure (kPa)
        svp = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        # Actual vapor pressure
        avp = svp * (humidity_percent / 100.0)
        # VPD
        vpd = svp - avp
        return round(vpd, 2)
    except:
        return None

def get_sensor_readings():
    """Get readings from both sensors"""
    sht45_data = read_sht45()
    hdc3022_data = read_hdc3022()
    
    # Calculate averages if both sensors are working
    avg_temp = None
    avg_humidity = None
    
    valid_temps = []
    valid_humidities = []
    
    if sht45_data and sht45_data["temperature"] is not None:
        valid_temps.append(sht45_data["temperature"])
        valid_humidities.append(sht45_data["humidity"])
    
    if hdc3022_data and hdc3022_data["temperature"] is not None:
        valid_temps.append(hdc3022_data["temperature"])
        valid_humidities.append(hdc3022_data["humidity"])
    
    if valid_temps:
        avg_temp = round(sum(valid_temps) / len(valid_temps), 1)
        avg_humidity = round(sum(valid_humidities) / len(valid_humidities), 1)
    
    # Calculate VPD
    vpd = calculate_vpd(avg_temp, avg_humidity)
    
    return {
        "timestamp": time.monotonic(),
        "sht45": sht45_data,
        "hdc3022": hdc3022_data,
        "averages": {
            "temperature": avg_temp,
            "humidity": avg_humidity,
            "vpd": vpd
        },
        "sensor_count": len(valid_temps)
    }

# Main reading loop
print("\n🔄 Starting sensor reading loop...")
print("📊 Format: [Time] SHT45 | HDC3022 | Average")
print("-" * 60)

reading_count = 0
while reading_count < 20:  # Run 20 readings for testing
    try:
        data = get_sensor_readings()
        reading_count += 1
        
        # Format output
        timestamp = f"[{reading_count:03d}]"
        
        # SHT45 status
        if data["sht45"] and data["sht45"]["temperature"] is not None:
            sht45_str = f"SHT45: {data['sht45']['temperature']}°C, {data['sht45']['humidity']}%"
        else:
            sht45_str = f"SHT45: ERROR ({data['sht45']['status'] if data['sht45'] else 'None'})"
        
        # HDC3022 status
        if data["hdc3022"] and data["hdc3022"]["temperature"] is not None:
            hdc3022_str = f"HDC3022: {data['hdc3022']['temperature']}°C, {data['hdc3022']['humidity']}%"
        else:
            hdc3022_str = f"HDC3022: ERROR ({data['hdc3022']['status'] if data['hdc3022'] else 'None'})"
        
        # Average status
        if data["averages"]["temperature"] is not None:
            avg_str = f"Avg: {data['averages']['temperature']}°C, {data['averages']['humidity']}%, VPD: {data['averages']['vpd']}"
        else:
            avg_str = "Avg: No valid data"
        
        print(f"{timestamp} {sht45_str}")
        print(f"     {hdc3022_str}")
        print(f"     {avg_str}")
        print(f"     Sensors working: {data['sensor_count']}/2")
        print()
        
        # JSON output for debugging
        if reading_count % 5 == 0:
            print("📋 JSON Debug:")
            json_str = json.dumps(data)
            print(json_str)
            print()
        
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        break
    except Exception as e:
        print(f"❌ Main loop error: {e}")
        time.sleep(1)

print("\n✅ Sensor reading test complete!")
print("📊 Summary:")
print(f"   - SHT45: {'✅ Working' if sht45 else '❌ Failed'}")
print(f"   - HDC3022: {'⚠️ Detected but invalid readings' if hdc3022 else '❌ Failed'}")
print(f"   - Total readings: {reading_count}")

# Cleanup
i2c1.deinit()
i2c2.deinit()

print("\n🎯 Next steps:")
print("   1. Check HDC3022 wiring and power")
print("   2. Verify HDC3022 STEMMA QT connection")
print("   3. Consider HDC3022 initialization sequence")
print("   4. Deploy working code with SHT45 primary sensor")
