#!/bin/bash

echo "🔧 Setting up InfluxDB 2.x..."

# Check if InfluxDB is already set up
SETUP_CHECK=$(curl -s http://localhost:8086/api/v2/setup | jq -r '.allowed' 2>/dev/null)

if [ "$SETUP_CHECK" = "false" ]; then
    echo "✅ InfluxDB is already set up"
else
    echo "🚀 Running initial InfluxDB setup..."
    
    # Setup InfluxDB with initial user, org, and bucket
    influx setup \
        --username admin \
        --password greenhouse123 \
        --org greenhouse \
        --bucket sensors \
        --retention 720h \
        --force
        
    if [ $? -eq 0 ]; then
        echo "✅ InfluxDB setup completed successfully"
    else
        echo "❌ InfluxDB setup failed"
        exit 1
    fi
fi

# Create API token for Grafana
echo "🔑 Creating API token for Grafana..."
TOKEN=$(influx auth create \
    --org greenhouse \
    --all-access \
    --description "Grafana Access Token" \
    --json | jq -r '.token' 2>/dev/null)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "null" ]; then
    echo "✅ API Token created: $TOKEN"
    echo "$TOKEN" > /home/lio/github/integration/infrastructure/influxdb_token.txt
    chmod 600 /home/lio/github/integration/infrastructure/influxdb_token.txt
    echo "Token saved to: influxdb_token.txt"
else
    echo "⚠️ Could not create new token, checking existing tokens..."
    influx auth list --org greenhouse --json | jq -r '.[0].token' > /home/lio/github/integration/infrastructure/influxdb_token.txt 2>/dev/null
    TOKEN=$(cat /home/lio/github/integration/infrastructure/influxdb_token.txt)
    echo "Using existing token: $TOKEN"
fi

echo ""
echo "📊 InfluxDB 2.x Configuration for Grafana:"
echo "============================================="
echo "URL: http://localhost:8086"
echo "Organization: greenhouse"
echo "Bucket: sensors"
echo "Token: $TOKEN"
echo ""
echo "🌐 Access InfluxDB UI at: http://localhost:8086"
echo "Login: admin / greenhouse123"
