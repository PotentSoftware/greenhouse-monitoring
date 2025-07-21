#!/bin/bash

# Deployment script for BeaglePlay greenhouse monitoring system
# This script transfers files and sets up the integrated dashboard

BEAGLEPLAY_IP="192.168.1.203"
BEAGLEPLAY_USER="debian"
LOCAL_CODE_DIR="/home/lio/github/greenhouse-monitoring/beagleplay_code"

echo "🌱 Deploying Greenhouse Monitoring System to BeaglePlay..."

# Check if BeaglePlay is accessible
echo "📡 Checking BeaglePlay connectivity..."
if ! ping -c 1 "$BEAGLEPLAY_IP" > /dev/null 2>&1; then
    echo "❌ Error: Cannot reach BeaglePlay at $BEAGLEPLAY_IP"
    echo "Please ensure USB connection is active and BeaglePlay is powered on"
    exit 1
fi

echo "✅ BeaglePlay is accessible"

# Transfer the updated Python web server
echo "📤 Transferring updated web server..."
scp "$LOCAL_CODE_DIR/ph_web_server.py" "$BEAGLEPLAY_USER@$BEAGLEPLAY_IP:/home/debian/"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to transfer ph_web_server.py"
    exit 1
fi

echo "✅ Web server transferred successfully"

# Create/update systemd service for the integrated dashboard
echo "🔧 Setting up systemd service..."

# Create service file content
cat > /tmp/integrated-greenhouse.service << EOF
[Unit]
Description=Integrated Greenhouse Monitoring Dashboard
After=network.target
Wants=network.target

[Service]
Type=simple
User=debian
WorkingDirectory=/home/debian
ExecStart=/usr/bin/python3 /home/debian/ph_web_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Transfer and install service
scp /tmp/integrated-greenhouse.service "$BEAGLEPLAY_USER@$BEAGLEPLAY_IP:/tmp/"

# Execute commands on BeaglePlay to setup service
ssh "$BEAGLEPLAY_USER@$BEAGLEPLAY_IP" << 'REMOTE_COMMANDS'
    echo "🔧 Installing systemd service..."
    
    # Move service file
    sudo mv /tmp/integrated-greenhouse.service /etc/systemd/system/
    
    # Stop any existing services that might conflict
    sudo systemctl stop ph-web-server 2>/dev/null || true
    sudo systemctl disable ph-web-server 2>/dev/null || true
    
    # Enable and start new service
    sudo systemctl daemon-reload
    sudo systemctl enable integrated-greenhouse.service
    sudo systemctl start integrated-greenhouse.service
    
    # Check service status
    echo "📊 Service status:"
    sudo systemctl status integrated-greenhouse.service --no-pager -l
    
    echo ""
    echo "🔍 Checking if port 8080 is listening..."
    if netstat -tuln | grep -q ":8080 "; then
        echo "✅ Port 8080 is active"
    else
        echo "⚠️  Port 8080 not yet active, service may still be starting..."
    fi
    
    echo ""
    echo "📋 Recent service logs:"
    sudo journalctl -u integrated-greenhouse.service -n 10 --no-pager
REMOTE_COMMANDS

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📡 Your integrated dashboard is now available at:"
    echo "   🌐 http://$BEAGLEPLAY_IP:8080/"
    echo ""
    echo "🔧 Service management commands:"
    echo "   Status: sudo systemctl status integrated-greenhouse.service"
    echo "   Restart: sudo systemctl restart integrated-greenhouse.service"
    echo "   Logs: sudo journalctl -u integrated-greenhouse.service -f"
    echo ""
    echo "📝 Features included:"
    echo "   ✅ Dark mode interface"
    echo "   ✅ Landscape layout"
    echo "   ✅ Real-time timestamps"
    echo "   ✅ BeagleConnect Freedom sensor data"
    echo "   ✅ Thermal camera statistics"
    echo "   ✅ Auto-restart after power failures"
    echo ""
    echo "⚠️  If BeagleConnect data shows 0s, check sensor connections and IIO device paths"
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi

# Clean up temporary files
rm -f /tmp/integrated-greenhouse.service

echo "🧹 Cleanup completed"
