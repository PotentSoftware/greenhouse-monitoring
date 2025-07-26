"""
WiFi Configuration for Feather S3[D]
Update with your actual WiFi credentials before deployment
"""

# WiFi Network Settings - UPDATE THESE!
WIFI_SSID = "YourWiFiNetwork"  # Replace with your WiFi network name
WIFI_PASSWORD = "YourWiFiPassword"  # Replace with your WiFi password

# Server Configuration
SERVER_PORT = 8080
SENSOR_READ_INTERVAL = 5  # seconds

# Optional: Static IP Configuration (uncomment if needed)
# STATIC_IP = "192.168.1.150"
# GATEWAY = "192.168.1.1"
# SUBNET = "255.255.255.0"
# DNS = "8.8.8.8"

print("📡 WiFi Configuration Loaded")
print(f"   SSID: {WIFI_SSID}")
print(f"   Port: {SERVER_PORT}")
print(f"   Interval: {SENSOR_READ_INTERVAL}s")
