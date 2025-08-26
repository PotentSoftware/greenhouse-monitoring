#!/bin/bash
# Complete Jetson Deployment - Independent Operation
# Deploys both Jetson server and Streamlit dashboard to Jetson for standalone operation

set -e

# Configuration
JETSON_USER="lionel"
JETSON_IP="192.168.1.75"
JETSON_HOST="${JETSON_USER}@${JETSON_IP}"
JETSON_PASSWORD="357843"
LOCAL_DIR="/home/lio/github/greenhouse-monitoring/jetson-orin-integration"
REMOTE_DIR="/home/lionel/jetson-greenhouse"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}🚀 Deploying Complete Jetson Greenhouse System${NC}"
echo "=================================================="
echo "Target: ${JETSON_HOST}"
echo "Remote directory: ${REMOTE_DIR}"
echo ""

# Test connectivity
echo -e "${YELLOW}Testing Jetson connectivity...${NC}"
if ! ping -c 1 ${JETSON_IP} > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot reach Jetson at ${JETSON_IP}${NC}"
    exit 1
fi

# Create remote directory structure
echo -e "${YELLOW}Setting up remote directories...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "mkdir -p ${REMOTE_DIR}/{src,config,data}"

# Transfer core files
echo -e "${YELLOW}Transferring core system files...${NC}"
sshpass -p "${JETSON_PASSWORD}" scp src/jetson_greenhouse_server.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/sensor_manager.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/vpd_calculator.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/time_series_plotter.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/thermal_processor.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/thermal_image_collector.py ${JETSON_HOST}:${REMOTE_DIR}/src/
sshpass -p "${JETSON_PASSWORD}" scp src/thermal_image_analyzer.py ${JETSON_HOST}:${REMOTE_DIR}/src/

# Transfer Streamlit files
echo -e "${YELLOW}Transferring Streamlit dashboard...${NC}"
sshpass -p "${JETSON_PASSWORD}" scp streamlit_dashboard.py ${JETSON_HOST}:${REMOTE_DIR}/
sshpass -p "${JETSON_PASSWORD}" scp src/streamlit_data_adapter.py ${JETSON_HOST}:${REMOTE_DIR}/src/

# Transfer configuration
echo -e "${YELLOW}Transferring configuration files...${NC}"
sshpass -p "${JETSON_PASSWORD}" scp config/jetson_config.py ${JETSON_HOST}:${REMOTE_DIR}/config/

# Transfer requirements and service files
sshpass -p "${JETSON_PASSWORD}" scp requirements.txt ${JETSON_HOST}:${REMOTE_DIR}/

# Create updated service files for Jetson
echo -e "${YELLOW}Creating service files...${NC}"

# Jetson server service
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cat > ${REMOTE_DIR}/jetson-greenhouse.service << 'EOF'
[Unit]
Description=Jetson Greenhouse Monitoring Server
After=network.target
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=lionel
Group=lionel
WorkingDirectory=${REMOTE_DIR}
Environment=PATH=${REMOTE_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${REMOTE_DIR}/src:${REMOTE_DIR}/config
ExecStart=${REMOTE_DIR}/venv/bin/python src/jetson_greenhouse_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jetson-greenhouse

[Install]
WantedBy=multi-user.target
EOF"

# Streamlit service
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cat > ${REMOTE_DIR}/jetson-streamlit.service << 'EOF'
[Unit]
Description=Jetson Greenhouse Streamlit Dashboard
After=network.target jetson-greenhouse.service
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=lionel
Group=lionel
WorkingDirectory=${REMOTE_DIR}
Environment=PATH=${REMOTE_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${REMOTE_DIR}/src:${REMOTE_DIR}/config
ExecStart=${REMOTE_DIR}/venv/bin/streamlit run streamlit_dashboard.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=jetson-streamlit

[Install]
WantedBy=multi-user.target
EOF"

# Setup Python environment and install dependencies
echo -e "${YELLOW}Setting up Python environment on Jetson...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cd ${REMOTE_DIR} && python3 -m venv venv"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cd ${REMOTE_DIR} && source venv/bin/activate && pip install --upgrade pip"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cd ${REMOTE_DIR} && source venv/bin/activate && pip install -r requirements.txt"

# Install and start services
echo -e "${YELLOW}Installing and starting services...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S cp ${REMOTE_DIR}/jetson-greenhouse.service /etc/systemd/system/"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S cp ${REMOTE_DIR}/jetson-streamlit.service /etc/systemd/system/"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl daemon-reload"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl enable jetson-greenhouse.service"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl enable jetson-streamlit.service"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl restart jetson-greenhouse.service"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl restart jetson-streamlit.service"

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check service status
echo -e "${BLUE}Service Status:${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl status jetson-greenhouse.service --no-pager"
echo ""
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl status jetson-streamlit.service --no-pager"

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=================================================="
echo -e "${GREEN}🌐 Jetson Server:${NC} http://${JETSON_IP}:8082/"
echo -e "${GREEN}📊 Streamlit Dashboard:${NC} http://${JETSON_IP}:8501/"
echo ""
echo -e "${BLUE}Service Management:${NC}"
echo "  Start:   sudo systemctl start jetson-greenhouse.service"
echo "  Stop:    sudo systemctl stop jetson-greenhouse.service"
echo "  Restart: sudo systemctl restart jetson-greenhouse.service"
echo "  Logs:    sudo journalctl -u jetson-greenhouse.service -f"
echo ""
echo "  Start:   sudo systemctl start jetson-streamlit.service"
echo "  Stop:    sudo systemctl stop jetson-streamlit.service"
echo "  Restart: sudo systemctl restart jetson-streamlit.service"
echo "  Logs:    sudo journalctl -u jetson-streamlit.service -f"
echo ""
echo -e "${GREEN}🎉 Jetson is now operating independently!${NC}"
