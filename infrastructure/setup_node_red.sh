#!/bin/bash

# Node-RED Setup and Dashboard Access Script
echo "=== Node-RED Setup ==="

# Check if Node-RED is running
if pgrep -f "node-red" > /dev/null; then
    echo "✓ Node-RED is running"
else
    echo "Starting Node-RED..."
    node-red > /home/lio/github/integration/infrastructure/node-red.log 2>&1 &
    sleep 3
    echo "✓ Node-RED started"
fi

echo ""
echo "=== Import Your Flow ==="
echo "1. Open Node-RED editor: http://127.0.0.1:1880"
echo "2. Click the hamburger menu (☰) in the top-right"
echo "3. Select 'Import'"
echo "4. Copy and paste the content from:"
echo "   /home/lio/github/integration/node-red-flows/greenhouse_integration.json"
echo "5. Click 'Import' and then 'Deploy'"
echo ""
echo "=== Access Your Dashboard ==="
echo "Node-RED Dashboard: http://127.0.0.1:1880/ui"
echo ""
echo "=== Useful URLs ==="
echo "• Node-RED Editor: http://127.0.0.1:1880"
echo "• Dashboard: http://127.0.0.1:1880/ui"
echo "• Debug Panel: Available in the Node-RED editor"
echo ""
echo "=== Your Configured Devices ==="
echo "• BeaglePlay: http://beagleplay.local:8080/api/sensors"
echo "• ESP32-S3 Thermal: http://192.168.1.100/api/thermal"
echo ""
echo "=== Monitoring ==="
echo "• Poll BeaglePlay every 30 seconds"
echo "• Poll ESP32-S3 every 15 seconds"
echo "• Data stored in InfluxDB"
echo "• VPD calculations and dashboard display"