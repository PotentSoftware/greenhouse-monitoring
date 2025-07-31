#!/bin/bash
# Simple connection to tCam-Mini using direct nmcli

echo "🔄 Connecting to tCam-Mini AP (Simple Method)"
echo "============================================="

# Disconnect current connection
echo "📡 Disconnecting current connection..."
sudo nmcli device disconnect wlo1 2>/dev/null
sleep 2

# Try direct connection without creating a profile
echo "🔗 Connecting directly to tCam-Mini-CDE9..."
sudo nmcli device wifi connect "tCam-Mini-CDE9" ifname wlo1

# Wait for connection
sleep 5

# Check connection status
echo "📊 Checking connection status..."
CURRENT=$(nmcli -t -f active,ssid dev wifi | grep "^yes" | cut -d: -f2)

if [[ "$CURRENT" == "tCam-Mini-CDE9" ]]; then
    echo "✅ Connected to tCam-Mini network!"
    
    # Get IP address
    IP=$(ip addr show wlo1 | grep "inet 192.168.4" | awk '{print $2}' | cut -d/ -f1)
    if [ -n "$IP" ]; then
        echo "📍 Your IP: $IP"
        echo "📍 tCam-Mini IP: 192.168.4.1"
        
        # Test connectivity
        echo "🔍 Testing connectivity..."
        if ping -c 2 -W 3 192.168.4.1 > /dev/null 2>&1; then
            echo "✅ tCam-Mini is reachable!"
            echo "🎯 Ready for data capture!"
        else
            echo "⚠️  Connected but cannot ping tCam-Mini"
            echo "   Waiting a bit more for network setup..."
            sleep 3
            if ping -c 1 -W 2 192.168.4.1 > /dev/null 2>&1; then
                echo "✅ tCam-Mini is now reachable!"
            else
                echo "❌ Still cannot reach tCam-Mini"
            fi
        fi
    else
        echo "⚠️  Connected but no IP on 192.168.4.x network"
        echo "   Current IP configuration:"
        ip addr show wlo1 | grep inet
    fi
else
    echo "❌ Failed to connect to tCam-Mini network"
    echo "📊 Current connection: $CURRENT"
    echo "🔍 Available networks:"
    nmcli device wifi list | grep -E "tCam|SSID"
fi
