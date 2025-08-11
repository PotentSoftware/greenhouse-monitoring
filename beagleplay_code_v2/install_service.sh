#!/bin/bash

# Installation script for Precision Sensors Server systemd service
# Run this script on the BeaglePlay to set up automatic startup

echo "🚀 Installing Precision Sensors Server systemd service..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run with sudo privileges"
    echo "Usage: sudo ./install_service.sh"
    exit 1
fi

# Check if service file exists
if [ ! -f "/tmp/precision-sensors.service" ]; then
    echo "❌ Service file not found at /tmp/precision-sensors.service"
    echo "Please copy the service file to /tmp/ first"
    exit 1
fi

# Check if startup script exists
if [ ! -f "/home/debian/start_precision_server.sh" ]; then
    echo "❌ Startup script not found at /home/debian/start_precision_server.sh"
    echo "Please copy the startup script first"
    exit 1
fi

# Stop any existing precision sensors services
echo "🛑 Stopping any existing services..."
systemctl stop precision-sensors.service 2>/dev/null || true
systemctl disable precision-sensors.service 2>/dev/null || true

# Remove old service files
rm -f /etc/systemd/system/precision-sensors.service
rm -f /etc/systemd/system/greenhouse-webserver.service

# Install new service
echo "📦 Installing new service..."
cp /tmp/precision-sensors.service /etc/systemd/system/
chmod 644 /etc/systemd/system/precision-sensors.service

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Enable service for automatic startup
echo "✅ Enabling service for automatic startup..."
systemctl enable precision-sensors.service

# Start the service
echo "🚀 Starting service..."
systemctl start precision-sensors.service

# Wait a moment for startup
sleep 5

# Check service status
echo "📊 Checking service status..."
if systemctl is-active --quiet precision-sensors.service; then
    echo "✅ Service is running successfully!"
    
    # Show service status
    systemctl status precision-sensors.service --no-pager -l
    
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📋 Service Management Commands:"
    echo "   Start:   sudo systemctl start precision-sensors.service"
    echo "   Stop:    sudo systemctl stop precision-sensors.service"
    echo "   Restart: sudo systemctl restart precision-sensors.service"
    echo "   Status:  sudo systemctl status precision-sensors.service"
    echo "   Logs:    sudo journalctl -u precision-sensors.service -f"
    echo ""
    echo "📁 Log Files:"
    echo "   Startup: /home/debian/precision_server_startup.log"
    echo "   Server:  /home/debian/precision_server.log"
    echo ""
    echo "🌐 Dashboard: http://192.168.1.203:8081/"
    
else
    echo "❌ Service failed to start!"
    echo "📋 Service status:"
    systemctl status precision-sensors.service --no-pager -l
    echo ""
    echo "📋 Recent logs:"
    journalctl -u precision-sensors.service --no-pager -l -n 20
    exit 1
fi
