#!/bin/bash
# Deploy Nginx Reverse Proxy for Jetson Greenhouse System
# Serves both Jetson server and Streamlit dashboard on port 8082

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

echo -e "${GREEN}🔧 Deploying Nginx Reverse Proxy Setup${NC}"
echo "=================================================="
echo "Target: ${JETSON_HOST}"
echo "Proxy will serve both services on port 8082"
echo ""

# Install nginx if not present
echo -e "${YELLOW}Installing nginx...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S apt update"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S apt install -y nginx"

# Stop nginx default service
echo -e "${YELLOW}Stopping default nginx service...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl stop nginx"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl disable nginx"

# Transfer nginx configuration
echo -e "${YELLOW}Transferring nginx configuration...${NC}"
sshpass -p "${JETSON_PASSWORD}" scp nginx-greenhouse.conf ${JETSON_HOST}:${REMOTE_DIR}/

# Update Jetson server to run on port 8083
echo -e "${YELLOW}Updating Jetson server configuration...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "sed -i 's/SERVER_PORT = 8082/SERVER_PORT = 8083/' ${REMOTE_DIR}/config/jetson_config.py"

# Create updated service files
echo -e "${YELLOW}Creating updated service files...${NC}"

# Nginx service
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cat > ${REMOTE_DIR}/jetson-nginx.service << 'EOF'
[Unit]
Description=Jetson Greenhouse Nginx Reverse Proxy
After=network.target jetson-greenhouse.service jetson-streamlit.service
Wants=network-online.target
After=network-online.target

[Service]
Type=forking
User=root
PIDFile=/run/nginx.pid
ExecStartPre=/usr/sbin/nginx -t -c ${REMOTE_DIR}/nginx-greenhouse.conf
ExecStart=/usr/sbin/nginx -c ${REMOTE_DIR}/nginx-greenhouse.conf
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
KillSignal=SIGTERM
PrivateTmp=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Update nginx config to use absolute paths
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "cat > ${REMOTE_DIR}/nginx-greenhouse.conf << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    access_log /var/log/nginx/access.log;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    server {
        listen 8082;
        server_name localhost 192.168.1.75;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection \"1; mode=block\";
        
        # Increase client max body size
        client_max_body_size 10M;
        
        # API routes - proxy to Jetson server on port 8083
        location /api/ {
            proxy_pass http://localhost:8083/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \"upgrade\";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;
            proxy_read_timeout 86400;
        }
        
        # Static files from Jetson server
        location ~ ^/(thermal_image\.png|plots\.png|static/) {
            proxy_pass http://localhost:8083;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            expires 1m;
            add_header Cache-Control \"public, immutable\";
        }
        
        # Streamlit WebSocket connections
        location /_stcore/stream {
            proxy_pass http://localhost:8501/_stcore/stream;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \"upgrade\";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;
            proxy_read_timeout 86400;
        }
        
        # Streamlit static files
        location /static/ {
            proxy_pass http://localhost:8501/static/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            expires 1d;
            add_header Cache-Control \"public, immutable\";
        }
        
        # Streamlit vendor files
        location /vendor/ {
            proxy_pass http://localhost:8501/vendor/;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            expires 1d;
            add_header Cache-Control \"public, immutable\";
        }
        
        # All other requests go to Streamlit dashboard
        location / {
            proxy_pass http://localhost:8501/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \"upgrade\";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_cache_bypass \$http_upgrade;
            proxy_read_timeout 86400;
        }
    }
}
EOF"

# Install and start services
echo -e "${YELLOW}Installing and starting services...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S cp ${REMOTE_DIR}/jetson-nginx.service /etc/systemd/system/"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl daemon-reload"

# Restart Jetson server with new port
echo -e "${YELLOW}Restarting Jetson server on port 8083...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl restart jetson-greenhouse.service"

# Restart Streamlit
echo -e "${YELLOW}Restarting Streamlit service...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl restart jetson-streamlit.service"

# Enable and start nginx proxy
echo -e "${YELLOW}Starting nginx reverse proxy...${NC}"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl enable jetson-nginx.service"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl start jetson-nginx.service"

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 8

# Check service status
echo -e "${BLUE}Service Status:${NC}"
echo "Jetson Server (port 8083):"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl status jetson-greenhouse.service --no-pager -l"
echo ""
echo "Streamlit Dashboard (port 8501):"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl status jetson-streamlit.service --no-pager -l"
echo ""
echo "Nginx Reverse Proxy (port 8082):"
sshpass -p "${JETSON_PASSWORD}" ssh ${JETSON_HOST} "echo '${JETSON_PASSWORD}' | sudo -S systemctl status jetson-nginx.service --no-pager -l"

echo ""
echo -e "${GREEN}✅ Nginx Reverse Proxy Deployment Complete!${NC}"
echo "=================================================="
echo -e "${GREEN}🌐 Unified Access Point:${NC} http://${JETSON_IP}:8082/"
echo -e "${GREEN}📊 Dashboard:${NC} http://${JETSON_IP}:8082/ (root path)"
echo -e "${GREEN}🔌 API Endpoints:${NC} http://${JETSON_IP}:8082/api/*"
echo ""
echo -e "${BLUE}Architecture:${NC}"
echo "  Port 8082 (nginx) -> Port 8501 (Streamlit) for dashboard"
echo "  Port 8082 (nginx) -> Port 8083 (Jetson API) for /api/* routes"
echo ""
echo -e "${GREEN}🎉 Both services now accessible via single port 8082!${NC}"
