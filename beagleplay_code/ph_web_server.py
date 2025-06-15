import http.server
import socketserver
import random
import time
import threading
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(filename='sensor_server.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Sensor reading functions
def read_sensor_value(device_path, sensor_type):
    try:
        with open(device_path, 'r') as f:
            value = float(f.read().strip())
            # Convert raw value to appropriate units
            if sensor_type == 'temp':
                value = value / 1000.0  # Convert millidegrees to degrees
            elif sensor_type == 'humidity':
                value = value / 1000.0  # Convert millipercent to percent
            return value
    except Exception as e:
        logging.error(f"Error reading sensor: {e}")
        return None

def find_iio_devices():
    devices = {}
    iio_path = "/sys/bus/iio/devices/"
    
    try:
        # List all IIO devices
        for device in os.listdir(iio_path):
            if device.startswith("iio:device"):
                device_path = os.path.join(iio_path, device)
                
                # Check if this is a temperature/humidity sensor
                if os.path.exists(os.path.join(device_path, "in_temp_input")):
                    devices["temp"] = os.path.join(device_path, "in_temp_input")
                
                if os.path.exists(os.path.join(device_path, "in_humidityrelative_input")):
                    devices["humidity"] = os.path.join(device_path, "in_humidityrelative_input")
    except Exception as e:
        logging.error(f"Error finding IIO devices: {e}")
    
    return devices

# Global variables for sensor data
ph_value = 7.0
temp_value = 25.0
humidity_value = 50.0
devices = find_iio_devices()

# Function to update sensor values
def update_sensor_data():
    global ph_value, temp_value, humidity_value
    
    while True:
        # Simulate pH value (replace with actual sensor reading)
        ph_value = round(random.uniform(6.5, 7.5), 2)
        
        # Read real temperature and humidity if available
        if "temp" in devices:
            temp_reading = read_sensor_value(devices["temp"], "temp")
            if temp_reading is not None:
                temp_value = temp_reading
        
        if "humidity" in devices:
            humidity_reading = read_sensor_value(devices["humidity"], "humidity")
            if humidity_reading is not None:
                humidity_value = humidity_reading
        
        # Log the values
        logging.info(f"Updated sensor values - pH: {ph_value}, Temp: {temp_value}°C, Humidity: {humidity_value}%")
        
        # Wait before next update
        time.sleep(5)

# Start the sensor update thread
sensor_thread = threading.Thread(target=update_sensor_data, daemon=True)
sensor_thread.start()

# HTTP request handler
class SensorHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Calculate VPD
            # VPD = (1 - RH/100) * SVP
            # SVP (Saturation Vapor Pressure) = 0.6108 * exp(17.27 * T / (T + 237.3))
            # where T is temperature in Celsius and RH is relative humidity in percent
            import math
            svp = 0.6108 * math.exp(17.27 * temp_value / (temp_value + 237.3))
            vpd = (1 - humidity_value / 100) * svp
            
            # Create HTML response
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sensor Data</title>
                <meta http-equiv="refresh" content="5">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .sensor-box {{ border: 1px solid #ddd; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                    .sensor-value {{ font-size: 24px; font-weight: bold; }}
                    .timestamp {{ color: #666; margin-top: 10px; }}
                </style>
            </head>
            <body>
                <h1>BeagleConnect Freedom Sensor Data</h1>
                
                <div class="sensor-box">
                    <h2>pH Value</h2>
                    <div class="sensor-value">{ph_value}</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Temperature</h2>
                    <div class="sensor-value">{temp_value:.2f} °C</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Humidity</h2>
                    <div class="sensor-value">{humidity_value:.2f} %</div>
                </div>
                
                <div class="sensor-box">
                    <h2>Vapor Pressure Deficit (VPD)</h2>
                    <div class="sensor-value">{vpd:.2f} kPa</div>
                </div>
                
                <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
            logging.info(f"Served sensor data - pH: {ph_value}, Temp: {temp_value}°C, Humidity: {humidity_value}%, VPD: {vpd:.2f} kPa")
            return
        
        # For JSON API endpoint
        elif self.path == '/api/sensors':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            
            # Calculate VPD
            svp = 0.6108 * math.exp(17.27 * temp_value / (temp_value + 237.3))
            vpd = (1 - humidity_value / 100) * svp
            
            data = {
                'ph': ph_value,
                'temperature': temp_value,
                'humidity': humidity_value,
                'vpd': round(vpd, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(data).encode())
            return
            
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        # Override to use our logger instead of printing to stderr
        logging.info("%s - %s" % (self.address_string(), format % args))

# Run the server
PORT = 8080
with socketserver.TCPServer(("", PORT), SensorHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}")
    logging.info(f"Server started on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        logging.info("Server stopped")
