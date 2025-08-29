#!/bin/bash
# Install systemd services for Jetson Greenhouse Monitoring

echo "Installing Jetson Greenhouse Monitoring Services..."

# Copy service files to systemd directory
sudo cp jetson-greenhouse.service /etc/systemd/system/
sudo cp tcam-proxy.service /etc/systemd/system/
sudo cp streamlit-dashboard.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable jetson-greenhouse.service
sudo systemctl enable tcam-proxy.service
sudo systemctl enable streamlit-dashboard.service

echo "✓ Services installed and enabled for auto-startup"
echo ""
echo "To start services now:"
echo "  sudo systemctl start jetson-greenhouse"
echo "  sudo systemctl start tcam-proxy"
echo "  sudo systemctl start streamlit-dashboard"
echo ""
echo "To check service status:"
echo "  sudo systemctl status jetson-greenhouse"
echo "  sudo systemctl status tcam-proxy"
echo "  sudo systemctl status streamlit-dashboard"
