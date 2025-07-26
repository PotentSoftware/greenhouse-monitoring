"""
Feather S3[D] WiFi HTTP Server for Dual Sensors
Production version with WiFi connectivity and HTTP API
"""

import time
import board
import busio
import json
import math
import wifi
import socketpool
import adafruit_httpserver
import microcontroller
import gc

# Import sensor libraries
import adafruit_sht4x
import adafruit_hdc302x

print("🌱 Feather S3[D] WiFi Sensor Server")
print("=" * 45)

# Configuration
WIFI_SSID = "YourWiFiNetwork"  # Replace with your WiFi network
WIFI_PASSWORD = "YourWiFiPassword"  # Replace with your WiFi password
SERVER_PORT = 8080
SENSOR_READ_INTERVAL = 5  # seconds

# Global variables for sensor data
latest_reading = {
    "timestamp": 0,
    "sht45": None,
    "hdc3022": None,
    "averages": {"temperature": None, "humidity": None, "vpd": None},
    "sensor_count": 0,
    "uptime": 0,
    "free_memory": 0
}

# Initialize I2C buses
print("🔧 Initializing I2C buses...")
i2c1 = busio.I2C(board.SCL, board.SDA)  # SHT45 sensor
i2c2 = board.I2C2()                     # HDC3022 sensor

# Initialize sensors
sht45 = None
hdc3022 = None

try:
    sht45 = adafruit_sht4x.SHT4x(i2c1)
    print("✅ SHT45 initialized on I2C1")
except Exception as e:
    print(f"❌ SHT45 initialization failed: {e}")

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
        
        if -40 <= temp <= 125 and 0 <= humidity <= 100:
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "status": "ok"
            }
        else:
            return {"temperature": None, "humidity": None, "status": "invalid_range"}
    except Exception as e:
        return {"temperature": None, "humidity": None, "status": f"error: {e}"}

def read_hdc3022():
    """Read HDC3022 sensor with error handling"""
    if not hdc3022:
        return None
    
    try:
        temp = hdc3022.temperature
        humidity = hdc3022.relative_humidity
        
        if -40 <= temp <= 125 and 0 <= humidity <= 100:
            return {
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "status": "ok"
            }
        else:
            return {"temperature": None, "humidity": None, "status": "invalid_range"}
    except Exception as e:
        return {"temperature": None, "humidity": None, "status": f"error: {e}"}

def calculate_vpd(temp_c, humidity_percent):
    """Calculate Vapor Pressure Deficit"""
    if temp_c is None or humidity_percent is None:
        return None
    
    try:
        svp = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        avp = svp * (humidity_percent / 100.0)
        vpd = svp - avp
        return round(vpd, 2)
    except:
        return None

def update_sensor_readings():
    """Update global sensor readings"""
    global latest_reading
    
    sht45_data = read_sht45()
    hdc3022_data = read_hdc3022()
    
    # Calculate averages
    valid_temps = []
    valid_humidities = []
    
    if sht45_data and sht45_data["temperature"] is not None:
        valid_temps.append(sht45_data["temperature"])
        valid_humidities.append(sht45_data["humidity"])
    
    if hdc3022_data and hdc3022_data["temperature"] is not None:
        valid_temps.append(hdc3022_data["temperature"])
        valid_humidities.append(hdc3022_data["humidity"])
    
    avg_temp = round(sum(valid_temps) / len(valid_temps), 1) if valid_temps else None
    avg_humidity = round(sum(valid_humidities) / len(valid_humidities), 1) if valid_humidities else None
    vpd = calculate_vpd(avg_temp, avg_humidity)
    
    latest_reading = {
        "timestamp": time.monotonic(),
        "sht45": sht45_data,
        "hdc3022": hdc3022_data,
        "averages": {
            "temperature": avg_temp,
            "humidity": avg_humidity,
            "vpd": vpd
        },
        "sensor_count": len(valid_temps),
        "uptime": time.monotonic(),
        "free_memory": gc.mem_free()
    }

# Connect to WiFi
print("\n📡 Connecting to WiFi...")
try:
    wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
    print(f"✅ Connected to {WIFI_SSID}")
    print(f"🌐 IP Address: {wifi.radio.ipv4_address}")
except Exception as e:
    print(f"❌ WiFi connection failed: {e}")
    print("🔄 Continuing in USB-only mode...")

# Create HTTP server
pool = socketpool.SocketPool(wifi.radio)
server = adafruit_httpserver.Server(pool, "/static", port=SERVER_PORT)

@server.route("/")
def base(request):
    """Root endpoint with basic info"""
    return adafruit_httpserver.Response(
        request,
        content_type="application/json",
        body=json.dumps({
            "device": "Feather S3[D] Dual Sensor Server",
            "version": "1.0.0",
            "endpoints": ["/", "/sensors", "/health", "/status"],
            "uptime": time.monotonic(),
            "ip": str(wifi.radio.ipv4_address) if wifi.radio.connected else "Not connected"
        })
    )

@server.route("/sensors")
def sensors(request):
    """Main sensor data endpoint"""
    return adafruit_httpserver.Response(
        request,
        content_type="application/json",
        body=json.dumps(latest_reading)
    )

@server.route("/health")
def health(request):
    """Health check endpoint"""
    return adafruit_httpserver.Response(
        request,
        content_type="application/json",
        body=json.dumps({
            "status": "healthy",
            "wifi_connected": wifi.radio.connected,
            "sensors_working": latest_reading["sensor_count"],
            "uptime": time.monotonic(),
            "free_memory": gc.mem_free()
        })
    )

@server.route("/status")
def status(request):
    """Detailed status endpoint"""
    return adafruit_httpserver.Response(
        request,
        content_type="application/json",
        body=json.dumps({
            "device_info": {
                "board_id": board.board_id,
                "cpu_frequency": microcontroller.cpu.frequency,
                "temperature": microcontroller.cpu.temperature
            },
            "network": {
                "wifi_connected": wifi.radio.connected,
                "ip_address": str(wifi.radio.ipv4_address) if wifi.radio.connected else None,
                "mac_address": str(wifi.radio.mac_address)
            },
            "sensors": {
                "sht45_available": sht45 is not None,
                "hdc3022_available": hdc3022 is not None,
                "last_reading": latest_reading
            },
            "system": {
                "uptime": time.monotonic(),
                "free_memory": gc.mem_free(),
                "read_interval": SENSOR_READ_INTERVAL
            }
        })
    )

# Start server
print(f"\n🚀 Starting HTTP server on port {SERVER_PORT}...")
try:
    server.start(str(wifi.radio.ipv4_address))
    print(f"✅ Server started at http://{wifi.radio.ipv4_address}:{SERVER_PORT}")
    print(f"📊 Sensor data: http://{wifi.radio.ipv4_address}:{SERVER_PORT}/sensors")
except Exception as e:
    print(f"❌ Server start failed: {e}")

# Main loop
print("\n🔄 Starting main sensor loop...")
print("📊 USB Serial Output | HTTP Server Running")
print("-" * 60)

last_sensor_read = 0
reading_count = 0

while True:
    try:
        current_time = time.monotonic()
        
        # Update sensor readings at specified interval
        if current_time - last_sensor_read >= SENSOR_READ_INTERVAL:
            update_sensor_readings()
            last_sensor_read = current_time
            reading_count += 1
            
            # Print to USB serial for monitoring
            data = latest_reading
            timestamp = f"[{reading_count:03d}]"
            
            if data["sht45"] and data["sht45"]["temperature"] is not None:
                sht45_str = f"SHT45: {data['sht45']['temperature']}°C, {data['sht45']['humidity']}%"
            else:
                sht45_str = "SHT45: ERROR"
            
            if data["hdc3022"] and data["hdc3022"]["temperature"] is not None:
                hdc3022_str = f"HDC3022: {data['hdc3022']['temperature']}°C, {data['hdc3022']['humidity']}%"
            else:
                hdc3022_str = "HDC3022: ERROR"
            
            if data["averages"]["temperature"] is not None:
                avg_str = f"Avg: {data['averages']['temperature']}°C, {data['averages']['humidity']}%, VPD: {data['averages']['vpd']}"
            else:
                avg_str = "Avg: No valid data"
            
            print(f"{timestamp} {sht45_str} | {hdc3022_str}")
            print(f"     {avg_str} | Sensors: {data['sensor_count']}/2 | Mem: {data['free_memory']}")
            
            # Garbage collection
            if reading_count % 10 == 0:
                gc.collect()
        
        # Handle HTTP requests
        try:
            server.poll()
        except Exception as e:
            print(f"⚠️ HTTP server error: {e}")
        
        time.sleep(0.1)  # Small delay to prevent overwhelming the CPU
        
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        break
    except Exception as e:
        print(f"❌ Main loop error: {e}")
        time.sleep(1)

# Cleanup
print("\n🧹 Cleaning up...")
try:
    server.stop()
    i2c1.deinit()
    i2c2.deinit()
    print("✅ Cleanup complete")
except:
    pass

print("👋 Feather S3[D] server stopped")
