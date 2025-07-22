#!/bin/bash

# Greenhouse Monitoring - Automated Sensor Setup Script
# This script configures the BeaglePlay for automatic sensor operation after reboot

set -e

BEAGLEPLAY_IP="192.168.1.203"
BEAGLEPLAY_USER="debian"
BEAGLEPLAY_PASS="temppwd"

echo "🌱 Setting up automated greenhouse sensor system..."

# Deploy updated Python web server
echo "📁 Deploying updated web server code..."
scp ph_web_server.py ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP}:/home/debian/

# Deploy custom gbridge service
echo "🔧 Deploying custom gbridge service..."
scp greenhouse-gbridge.service ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP}:/tmp/

# Configure services on BeaglePlay
echo "⚙️ Configuring services on BeaglePlay..."
ssh ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP} << 'EOF'
echo 'temppwd' | sudo -S bash << 'SUDO_EOF'

# Stop existing services
echo "Stopping existing services..."
systemctl stop beagleconnect-gateway.service || true
systemctl stop greenhouse-webserver.service || true

# Disable the default beagleconnect-gateway service to prevent conflicts
echo "Disabling default BeagleConnect gateway service..."
systemctl disable beagleconnect-gateway.service

# Install custom gbridge service
echo "Installing custom gbridge service..."
cp /tmp/greenhouse-gbridge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable greenhouse-gbridge.service

# Restart greenhouse web server service
echo "Starting greenhouse web server..."
systemctl restart greenhouse-webserver.service
systemctl enable greenhouse-webserver.service

# Start custom gbridge service
echo "Starting custom gbridge service..."
systemctl start greenhouse-gbridge.service

echo "✅ Services configured successfully!"

# Show service status
echo "📊 Service Status:"
systemctl status greenhouse-webserver.service --no-pager -l
echo ""
systemctl status greenhouse-gbridge.service --no-pager -l

SUDO_EOF
EOF

echo ""
echo "🎉 Automated setup complete!"
echo ""
echo "📊 System URLs:"
echo "   🌡️ Dashboard: http://${BEAGLEPLAY_IP}:8080/"
echo "   📊 API Data:  http://${BEAGLEPLAY_IP}:8080/api/data"
echo ""
echo "🔧 Service Management Commands:"
echo "   Check status: ssh ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP} 'sudo systemctl status greenhouse-gbridge.service'"
echo "   View logs:    ssh ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP} 'sudo journalctl -u greenhouse-gbridge.service -f'"
echo "   Restart:      ssh ${BEAGLEPLAY_USER}@${BEAGLEPLAY_IP} 'sudo systemctl restart greenhouse-gbridge.service'"
echo ""
echo "⏱️ Wait 30 seconds for services to fully start, then test:"
echo "   curl -s http://${BEAGLEPLAY_IP}:8080/api/data | jq '.temperature, .humidity, .light, .ph'"
echo ""
echo "✅ The system will now automatically start with real sensor data after every reboot!"
