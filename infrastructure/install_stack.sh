#!/bin/bash

# Installation script for IoT Integration Stack
# Self-hosted InfluxDB OSS + Grafana OSS + Node-RED

set -e

echo "🚀 Installing IoT Integration Stack..."

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install Node.js and npm for Node-RED
echo "📦 Installing Node.js and npm..."
sudo apt install -y nodejs npm curl wget

# Install Node-RED
echo "🔴 Installing Node-RED..."
sudo npm install -g --unsafe-perm node-red

# Install Node-RED nodes for our integration
echo "🔴 Installing Node-RED additional nodes..."
sudo npm install -g node-red-contrib-influxdb
sudo npm install -g node-red-dashboard
sudo npm install -g node-red-node-serialport

# Install InfluxDB OSS
echo "💾 Installing InfluxDB OSS..."
curl -fsSL https://repos.influxdata.com/influxdata-archive_compat.key | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo apt update
sudo apt install -y influxdb2

# Install Grafana OSS  
echo "📊 Installing Grafana OSS..."
sudo apt install -y software-properties-common apt-transport-https
wget -q -O - https://packages.grafana.com/gpg.key | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/grafana.gpg
echo "deb [signed-by=/etc/apt/trusted.gpg.d/grafana.gpg] https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y grafana

# Start services
echo "🔧 Starting services..."
sudo systemctl enable influxdb
sudo systemctl start influxdb
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Create InfluxDB setup script
cat > /home/lio/github/integration/infrastructure/setup_influxdb.sh << 'EOF'
#!/bin/bash
echo "Setting up InfluxDB..."
influx setup \
  --username admin \
  --password greenhouse123 \
  --org greenhouse \
  --bucket sensors \
  --retention 30d \
  --force
echo "InfluxDB setup complete!"
echo "Access InfluxDB at: http://localhost:8086"
echo "Username: admin"
echo "Password: greenhouse123"
EOF

chmod +x /home/lio/github/integration/infrastructure/setup_influxdb.sh

echo "✅ Installation complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Run: ./setup_influxdb.sh"
echo "2. Access Grafana at: http://localhost:3000 (admin/admin)"
echo "3. Start Node-RED with: node-red"
echo "4. Access Node-RED at: http://localhost:1880"
echo ""
echo "📊 Service status:"
sudo systemctl status influxdb --no-pager -l
sudo systemctl status grafana-server --no-pager -l
