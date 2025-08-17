#!/bin/bash
# Deploy Jetson Orin Nano Greenhouse Monitoring System
# Transfers files and installs system on remote Jetson

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
JETSON_USER="lionel"
JETSON_IP="192.168.1.75"
JETSON_HOST="${JETSON_USER}@${JETSON_IP}"
LOCAL_DIR="/home/lio/github/greenhouse-monitoring/jetson-orin-integration"
REMOTE_DIR="/tmp/jetson-greenhouse-deploy"

echo -e "${GREEN}🤖 Deploying Jetson Orin Nano Greenhouse Monitoring System${NC}"
echo "============================================================"
echo "Source: ${LOCAL_DIR}"
echo "Target: ${JETSON_HOST}"
echo "Remote staging: ${REMOTE_DIR}"
echo ""

# Check if Jetson is reachable
echo -e "${YELLOW}Testing Jetson connectivity...${NC}"
if ! ping -c 1 ${JETSON_IP} > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot reach Jetson at ${JETSON_IP}${NC}"
    echo "Please check:"
    echo "1. Jetson is powered on and connected to WiFi"
    echo "2. IP address is correct (${JETSON_IP})"
    echo "3. SSH is enabled on Jetson"
    exit 1
fi

if ! ssh -o ConnectTimeout=5 ${JETSON_HOST} "echo 'Connection test'" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot SSH to Jetson${NC}"
    echo "Please check SSH connectivity and credentials"
    exit 1
fi

echo -e "${GREEN}✅ Jetson connectivity verified${NC}"

# Create remote staging directory
echo -e "${YELLOW}Creating remote staging directory...${NC}"
ssh ${JETSON_HOST} "mkdir -p ${REMOTE_DIR}"

# Transfer files
echo -e "${YELLOW}Transferring files to Jetson...${NC}"
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    ${LOCAL_DIR}/ ${JETSON_HOST}:${REMOTE_DIR}/

echo -e "${GREEN}✅ Files transferred successfully${NC}"

# Run installation on Jetson
echo -e "${YELLOW}Running installation on Jetson...${NC}"
ssh ${JETSON_HOST} "cd ${REMOTE_DIR} && chmod +x install.sh && sudo ./install.sh"

# Test connectivity after installation
echo -e "${YELLOW}Testing sensor connectivity...${NC}"
ssh ${JETSON_HOST} "/home/${JETSON_USER}/jetson-greenhouse/test_connectivity.sh"

# Start the service
echo -e "${YELLOW}Starting Jetson greenhouse service...${NC}"
ssh ${JETSON_HOST} "sudo systemctl start jetson-greenhouse"

# Wait a moment for service to start
sleep 5

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
ssh ${JETSON_HOST} "sudo systemctl status jetson-greenhouse --no-pager -l"

# Test web interface
echo -e "${YELLOW}Testing web interface...${NC}"
if curl -s --connect-timeout 10 http://${JETSON_IP}:8082/ > /dev/null; then
    echo -e "${GREEN}✅ Web interface is accessible${NC}"
else
    echo -e "${RED}❌ Web interface not accessible${NC}"
    echo "Checking logs..."
    ssh ${JETSON_HOST} "sudo journalctl -u jetson-greenhouse --no-pager -l -n 20"
fi

# Clean up staging directory
echo -e "${YELLOW}Cleaning up staging directory...${NC}"
ssh ${JETSON_HOST} "rm -rf ${REMOTE_DIR}"

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "Access Points:"
echo "  Jetson Dashboard: http://${JETSON_IP}:8082/"
echo "  BeaglePlay Dashboard: http://192.168.1.203:8080/"
echo "  JSON API: http://${JETSON_IP}:8082/api/sensors"
echo ""
echo "Management Commands (run on Jetson):"
echo "  Status: /home/${JETSON_USER}/jetson-greenhouse/status.sh"
echo "  Logs: /home/${JETSON_USER}/jetson-greenhouse/logs.sh"
echo "  Test: /home/${JETSON_USER}/jetson-greenhouse/test_connectivity.sh"
echo ""
echo "Service Commands (run on Jetson):"
echo "  Start: sudo systemctl start jetson-greenhouse"
echo "  Stop: sudo systemctl stop jetson-greenhouse"
echo "  Restart: sudo systemctl restart jetson-greenhouse"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open Jetson dashboard: http://${JETSON_IP}:8082/"
echo "2. Compare with BeaglePlay: http://192.168.1.203:8080/"
echo "3. Monitor both systems for concurrent operation"
echo "4. Test system redundancy by stopping one system"
