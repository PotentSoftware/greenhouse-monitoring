#!/bin/bash
# Jetson Orin Nano Greenhouse Monitoring Installation Script
# Sets up the independent greenhouse monitoring system

set -e

echo "🤖 Jetson Orin Nano Greenhouse Monitoring Installation"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
JETSON_USER="lionel"
JETSON_IP="192.168.1.75"
INSTALL_DIR="/home/${JETSON_USER}/jetson-greenhouse"
SERVICE_NAME="jetson-greenhouse"
PYTHON_ENV="${INSTALL_DIR}/venv"

echo -e "${YELLOW}Installation Configuration:${NC}"
echo "User: ${JETSON_USER}"
echo "IP: ${JETSON_IP}"
echo "Install Directory: ${INSTALL_DIR}"
echo "Service: ${SERVICE_NAME}"
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo -e "${RED}Warning: This script is designed for Jetson devices${NC}"
    echo "Continuing anyway..."
fi

# Create installation directory
echo -e "${YELLOW}Creating installation directory...${NC}"
sudo mkdir -p ${INSTALL_DIR}
sudo chown ${JETSON_USER}:${JETSON_USER} ${INSTALL_DIR}

# Copy source files
echo -e "${YELLOW}Copying source files...${NC}"
cp -r src/ ${INSTALL_DIR}/
cp -r config/ ${INSTALL_DIR}/
cp -r templates/ ${INSTALL_DIR}/ 2>/dev/null || echo "No templates directory found"
cp requirements.txt ${INSTALL_DIR}/

# Create data directory
echo -e "${YELLOW}Creating data directory...${NC}"
mkdir -p /home/${JETSON_USER}/greenhouse-data
chown ${JETSON_USER}:${JETSON_USER} /home/${JETSON_USER}/greenhouse-data

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y libopencv-dev python3-opencv
sudo apt install -y build-essential cmake
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libatlas-base-dev gfortran

# Create Python virtual environment
echo -e "${YELLOW}Creating Python virtual environment...${NC}"
cd ${INSTALL_DIR}
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create systemd service file
echo -e "${YELLOW}Creating systemd service...${NC}"
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Jetson Orin Nano Greenhouse Monitoring Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${JETSON_USER}
WorkingDirectory=${INSTALL_DIR}
Environment=PATH=${PYTHON_ENV}/bin
ExecStart=${PYTHON_ENV}/bin/python src/jetson_greenhouse_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment variables
Environment=PYTHONPATH=${INSTALL_DIR}/src:${INSTALL_DIR}/config

[Install]
WantedBy=multi-user.target
EOF

# Create startup script
echo -e "${YELLOW}Creating startup script...${NC}"
tee ${INSTALL_DIR}/start_jetson_greenhouse.sh > /dev/null <<EOF
#!/bin/bash
# Jetson Greenhouse Monitoring Startup Script

cd ${INSTALL_DIR}
source venv/bin/activate

echo "🤖 Starting Jetson Orin Nano Greenhouse Monitoring..."
echo "Network: ${JETSON_IP}:8082"
echo "Concurrent with BeaglePlay: 192.168.1.203:8080"
echo ""

python src/jetson_greenhouse_server.py
EOF

chmod +x ${INSTALL_DIR}/start_jetson_greenhouse.sh

# Create management scripts
echo -e "${YELLOW}Creating management scripts...${NC}"

# Status script
tee ${INSTALL_DIR}/status.sh > /dev/null <<EOF
#!/bin/bash
echo "🤖 Jetson Greenhouse Monitoring Status"
echo "====================================="
echo ""

# Service status
echo "Service Status:"
sudo systemctl status ${SERVICE_NAME} --no-pager -l

echo ""
echo "Network Status:"
echo "Jetson Dashboard: http://${JETSON_IP}:8082/"
echo "BeaglePlay Dashboard: http://192.168.1.203:8080/"
echo ""

# Check if ports are listening
if netstat -tuln | grep -q ":8082 "; then
    echo "✅ Jetson server is listening on port 8082"
else
    echo "❌ Jetson server is NOT listening on port 8082"
fi

# Check sensor connectivity
echo ""
echo "Sensor Connectivity:"
if curl -s --connect-timeout 2 http://192.168.1.81:8080/sensors > /dev/null; then
    echo "✅ Feather S3[D] reachable at 192.168.1.81"
else
    echo "❌ Feather S3[D] NOT reachable at 192.168.1.81"
fi

if nc -z 192.168.1.130 5001 2>/dev/null; then
    echo "✅ tCam-Mini reachable at 192.168.1.130:5001"
else
    echo "❌ tCam-Mini NOT reachable at 192.168.1.130:5001"
fi
EOF

chmod +x ${INSTALL_DIR}/status.sh

# Logs script
tee ${INSTALL_DIR}/logs.sh > /dev/null <<EOF
#!/bin/bash
echo "🤖 Jetson Greenhouse Monitoring Logs"
echo "===================================="
echo ""

if [ "\$1" = "-f" ]; then
    echo "Following logs (Ctrl+C to exit)..."
    sudo journalctl -u ${SERVICE_NAME} -f
else
    echo "Recent logs (use -f to follow):"
    sudo journalctl -u ${SERVICE_NAME} --no-pager -l -n 50
fi
EOF

chmod +x ${INSTALL_DIR}/logs.sh

# Test connectivity script
tee ${INSTALL_DIR}/test_connectivity.sh > /dev/null <<EOF
#!/bin/bash
echo "🤖 Testing Sensor Connectivity"
echo "=============================="

cd ${INSTALL_DIR}
source venv/bin/activate

python3 -c "
import sys
sys.path.append('src')
sys.path.append('config')

from sensor_manager import SensorManager
import jetson_config as config
import logging

logging.basicConfig(level=logging.INFO)

print('Testing Feather S3[D] connection...')
sensor_manager = SensorManager(config)
feather_result = sensor_manager.fetch_feather_s3d_data()
print(f'Feather S3[D]: {\"✅ Connected\" if feather_result else \"❌ Failed\"}')

print('\\nTesting tCam-Mini connection...')
thermal_result = sensor_manager.fetch_thermal_data()
print(f'tCam-Mini: {\"✅ Connected\" if thermal_result else \"❌ Failed\"}')

print('\\nSensor data summary:')
data = sensor_manager.get_sensor_data()
print(f'Feather S3[D] Status: {data[\"feather_s3d\"][\"connection_status\"]}')
print(f'Thermal Camera Status: {data[\"thermal_camera\"][\"connection_status\"]}')
"
EOF

chmod +x ${INSTALL_DIR}/test_connectivity.sh

# Set ownership
sudo chown -R ${JETSON_USER}:${JETSON_USER} ${INSTALL_DIR}

# Enable and start service
echo -e "${YELLOW}Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo ""
echo -e "${GREEN}🎉 Installation Complete!${NC}"
echo ""
echo "Management Commands:"
echo "  Start service:    sudo systemctl start ${SERVICE_NAME}"
echo "  Stop service:     sudo systemctl stop ${SERVICE_NAME}"
echo "  Restart service:  sudo systemctl restart ${SERVICE_NAME}"
echo "  View status:      ${INSTALL_DIR}/status.sh"
echo "  View logs:        ${INSTALL_DIR}/logs.sh"
echo "  Test sensors:     ${INSTALL_DIR}/test_connectivity.sh"
echo ""
echo "Access Points:"
echo "  Jetson Dashboard: http://${JETSON_IP}:8082/"
echo "  BeaglePlay Dashboard: http://192.168.1.203:8080/"
echo "  JSON API: http://${JETSON_IP}:8082/api/sensors"
echo ""
echo "Next Steps:"
echo "1. Test connectivity: ${INSTALL_DIR}/test_connectivity.sh"
echo "2. Start the service: sudo systemctl start ${SERVICE_NAME}"
echo "3. Check status: ${INSTALL_DIR}/status.sh"
echo "4. Open dashboard: http://${JETSON_IP}:8082/"
echo ""
echo -e "${YELLOW}Note: The system will operate independently and concurrently with BeaglePlay${NC}"
