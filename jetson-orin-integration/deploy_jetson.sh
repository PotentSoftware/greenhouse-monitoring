#!/bin/bash
# Jetson Orin Nano Greenhouse Monitoring Deployment Script

set -e

echo "🚀 Deploying Jetson Greenhouse Monitoring System..."

# Configuration
PROJECT_DIR="/home/lio/github/greenhouse-monitoring/jetson-orin-integration"
DATA_DIR="/home/lio/jetson-greenhouse/data"
SERVICE_NAME="jetson-greenhouse"

# Create data directory
echo "📁 Creating data directory..."
mkdir -p "$DATA_DIR"

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install systemd service
echo "⚙️ Installing systemd service..."
sudo cp jetson-greenhouse.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Start the service
echo "🔄 Starting Jetson Greenhouse service..."
sudo systemctl restart $SERVICE_NAME

# Check service status
echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager

# Show access information
echo ""
echo "✅ Deployment complete!"
echo "🌐 Access the dashboard at: http://$(hostname -I | awk '{print $1}'):8082/"
echo "📋 Check logs with: sudo journalctl -u $SERVICE_NAME -f"
echo "🔧 Service control:"
echo "   Start:   sudo systemctl start $SERVICE_NAME"
echo "   Stop:    sudo systemctl stop $SERVICE_NAME"
echo "   Restart: sudo systemctl restart $SERVICE_NAME"
echo "   Status:  sudo systemctl status $SERVICE_NAME"
