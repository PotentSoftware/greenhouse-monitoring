#!/bin/bash
# Script to deploy the integrated greenhouse monitoring dashboard on BeaglePlay

echo "=== Deploying Integrated Greenhouse Monitoring Dashboard ==="
echo ""

# Check if we're running on BeaglePlay
if ! grep -q "BeaglePlay\|AM62" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed to run on BeaglePlay"
fi

echo "1. Configuring system timezone to UK..."
# Set timezone to UK (handles BST/GMT automatically)
sudo timedatectl set-timezone Europe/London
sudo timedatectl set-ntp true
echo "Current time: $(date)"

echo ""
echo "2. Installing Python dependencies..."
# Install requests library if not present
pip3 install requests --user

echo ""
echo "3. Stopping existing web server service..."
sudo systemctl stop ph-web-server.service

echo ""
echo "4. Ensuring Node-RED is running on port 1880..."
sudo systemctl enable node-red.service
sudo systemctl start node-red.service

echo ""
echo "5. Restarting integrated dashboard service on port 8080..."
sudo systemctl restart ph-web-server.service

echo ""
echo "6. Checking service status..."
sudo systemctl status ph-web-server.service --no-pager

echo ""
echo "7. Enabling services for automatic startup after power failures..."
sudo systemctl enable ph-web-server.service
sudo systemctl enable node-red.service

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Dashboard URLs:"
echo "• Integrated Dashboard (NEW): http://localhost:8080 or http://192.168.1.203:8080"
echo "• Node-RED Dashboard: http://localhost:1880/ui or http://192.168.1.203:1880/ui"
echo ""
echo "Features:"
echo "• ✓ Dark mode theme"
echo "• ✓ Landscape layout for HDMI display"
echo "• ✓ BeagleConnect Freedom sensor data"
echo "• ✓ Thermal camera statistics"
echo "• ✓ Real-time timestamp in header"
echo "• ✓ Automatic startup after power failures"
echo "• ✓ Integrated data from both sources"
echo ""
echo "The system will now operate independently with a dumb power supply."
