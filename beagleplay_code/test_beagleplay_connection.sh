#!/bin/bash

# Test script to check BeaglePlay connection and run the server directly
BEAGLEPLAY_IP="192.168.1.203"
BEAGLEPLAY_USER="debian"

echo "🧪 Testing BeaglePlay connection and running server directly..."

# Test the web server directly (without systemd)
echo "🚀 Starting web server directly on BeaglePlay..."
ssh "$BEAGLEPLAY_USER@$BEAGLEPLAY_IP" "cd /home/debian && python3 ph_web_server.py" &

SERVER_PID=$!
echo "📡 Server started with PID: $SERVER_PID"

echo "⏳ Waiting 10 seconds for server to start..."
sleep 10

echo "🌐 Testing web server accessibility..."
if curl -s "http://$BEAGLEPLAY_IP:8080/" > /dev/null; then
    echo "✅ Web server is accessible at http://$BEAGLEPLAY_IP:8080/"
    echo "🎉 You can now access your dashboard!"
else
    echo "❌ Web server is not accessible"
fi

echo ""
echo "📋 To stop the server, run: kill $SERVER_PID"
echo "🔍 To check logs, SSH to BeaglePlay and check sensor_server.log"
