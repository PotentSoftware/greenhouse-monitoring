#!/bin/bash

echo "🔍 Scanning for BeaglePlay and ESP32-S3 devices..."

# Get network range (try multiple common interfaces)
NETWORK=$(ip route | grep -E "(wlo1|wlan0|eth0|enp)" | grep 192.168 | head -1 | awk '{print $1}')
if [ -z "$NETWORK" ]; then
    NETWORK="192.168.1.0/24"
    echo "⚠️  Could not detect network, using default: $NETWORK"
else
    echo "Scanning network: $NETWORK"
fi

echo ""
echo "🔍 Looking for devices with web servers..."

# Scan for devices with web servers on common ports
for ip in $(seq 1 254); do
    target="192.168.1.$ip"
    
    # Quick check for HTTP servers
    if timeout 1 bash -c "echo >/dev/tcp/$target/80" 2>/dev/null; then
        echo "Found HTTP server at: $target"
        
        # Check if it responds to our API endpoints
        if curl -s --connect-timeout 2 "http://$target/api/sensors" | grep -q "ph\|temperature"; then
            echo "  ✅ Found BeaglePlay-like API at: http://$target:8080/api/sensors"
        fi
        
        if curl -s --connect-timeout 2 "http://$target/api/thermal" | grep -q "temp\|thermal"; then
            echo "  ✅ Found ESP32-S3-like API at: http://$target/api/thermal"
        fi
    fi
    
    # Check port 8080 for BeaglePlay
    if timeout 1 bash -c "echo >/dev/tcp/$target/8080" 2>/dev/null; then
        echo "Found server on port 8080 at: $target"
        if curl -s --connect-timeout 2 "http://$target:8080/api/sensors" | grep -q "ph\|temperature"; then
            echo "  ✅ Found BeaglePlay API at: http://$target:8080/api/sensors"
        fi
    fi
done

echo ""
echo "🔍 Trying mDNS discovery..."
avahi-browse -t -r _http._tcp 2>/dev/null | grep -E "(beagle|esp32|thermal)"

echo ""
echo "💡 Manual tests:"
echo "BeaglePlay: curl http://[IP]:8080/api/sensors"
echo "ESP32-S3:   curl http://[IP]/api/thermal"
