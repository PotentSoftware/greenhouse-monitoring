#!/bin/bash
# Robust connection to tCam-Mini AP

echo "🔄 Connecting to tCam-Mini AP (Robust Method)"
echo "=============================================="

# First, ensure we're disconnected
echo "📡 Disconnecting current connection..."
sudo nmcli device disconnect wlo1 2>/dev/null
sleep 2

# Remove any existing connection profile for tCam
echo "🗑️  Removing old tCam profiles..."
sudo nmcli connection delete "tCam-Mini-CDE9" 2>/dev/null
sleep 1

# Create a new connection profile
echo "📝 Creating new connection profile..."
sudo nmcli connection add \
    type wifi \
    con-name "tCam-Mini-CDE9" \
    ifname wlo1 \
    ssid "tCam-Mini-CDE9" \
    -- \
    wifi-sec.key-mgmt none \
    ipv4.method auto \
    ipv6.method ignore

# Connect using the profile
echo "🔗 Connecting to tCam-Mini..."
sudo nmcli connection up "tCam-Mini-CDE9"

# Wait for connection
sleep 3

# Check if we got the right IP
IP=$(ip addr show wlo1 | grep "inet 192.168.4" | awk '{print $2}' | cut -d/ -f1)
if [ -n "$IP" ]; then
    echo "✅ Connected successfully!"
    echo "📍 Your IP: $IP"
    echo "📍 tCam-Mini IP: 192.168.4.1"
    
    # Test connectivity
    if ping -c 1 -W 2 192.168.4.1 > /dev/null 2>&1; then
        echo "✅ tCam-Mini is reachable!"
    else
        echo "⚠️  Connected but cannot ping tCam-Mini"
        echo "   Trying to refresh connection..."
        sudo dhclient -r wlo1 2>/dev/null
        sudo dhclient wlo1 2>/dev/null
        sleep 2
        
        # Test again
        if ping -c 1 -W 2 192.168.4.1 > /dev/null 2>&1; then
            echo "✅ tCam-Mini is now reachable!"
        else
            echo "❌ Still cannot reach tCam-Mini"
        fi
    fi
else
    echo "❌ Failed to get IP on tCam network"
    echo "   Current IP:"
    ip addr show wlo1 | grep inet
fi
