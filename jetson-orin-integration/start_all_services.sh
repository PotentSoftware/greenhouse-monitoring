#!/bin/bash
# Start all greenhouse monitoring services on Jetson Orin Nano

echo "Starting Greenhouse Monitoring Services..."

# Kill any existing instances
echo "Stopping existing services..."
pkill -f "streamlit run"
pkill -f "tcam_proxy_server"
pkill -f "tcam_web_interface"
pkill -f "jetson_greenhouse_server"

sleep 2

# Start the sensor data server (if not already running as a service)
echo "Checking sensor data server..."
if ! curl -s http://192.168.1.81:8080/sensors > /dev/null 2>&1; then
    echo "Warning: ESP32-S3 sensor server not responding at 192.168.1.81:8080"
else
    echo "✓ ESP32-S3 sensor server is running"
fi

# Start the tCam web interface
echo "Starting tCam web interface..."
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts
nohup python3 tcam_web_interface.py > /tmp/tcam_web_interface.log 2>&1 &
echo "✓ tCam web interface started on port 8080"

# Start the tCam proxy server (as fallback)
echo "Starting tCam proxy server..."
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration/src
nohup python3 tcam_proxy_server.py > /tmp/tcam_proxy.log 2>&1 &
echo "✓ tCam proxy server started on port 5002 (fallback)"

# Wait for services to initialize
sleep 3

# Start the Streamlit dashboard
echo "Starting Streamlit dashboard..."
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration
source venv/bin/activate
nohup streamlit run streamlit_dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true > /tmp/streamlit.log 2>&1 &
echo "✓ Streamlit dashboard started on port 8501"

# Wait for services to start
sleep 5

# Check service status
echo ""
echo "Service Status:"
echo "---------------"

# Check Streamlit
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✓ Streamlit dashboard: Running at http://$(hostname -I | awk '{print $1}'):8501"
else
    echo "✗ Streamlit dashboard: Failed to start"
fi

# Check tCam web interface
if curl -s http://localhost:8080/status > /dev/null 2>&1; then
    echo "✓ tCam web interface: Running at http://localhost:8080"
    # Check if actually connected to tCam
    if curl -s http://localhost:8080/status | grep -q '"connected": true'; then
        echo "  └─ Connected to tCam-Mini at 192.168.1.130"
    else
        echo "  └─ Not connected to tCam-Mini (check network)"
    fi
else
    echo "✗ tCam web interface: Failed to start"
fi

# Check tCam proxy
if curl -s http://localhost:5002/status > /dev/null 2>&1; then
    echo "✓ tCam proxy server: Running at http://localhost:5002 (fallback)"
else
    echo "✗ tCam proxy server: Failed to start"
fi

# Check ESP32 sensors
if curl -s http://192.168.1.81:8080/sensors > /dev/null 2>&1; then
    echo "✓ ESP32-S3 sensors: Connected"
else
    echo "✗ ESP32-S3 sensors: Not reachable"
fi

echo ""
echo "Logs available at:"
echo "  - Streamlit: /tmp/streamlit.log"
echo "  - tCam web interface: /tmp/tcam_web_interface.log"
echo "  - tCam proxy: /tmp/tcam_proxy.log"
echo ""
echo "To stop all services, run: pkill -f 'streamlit|tcam_web_interface|tcam_proxy'"
