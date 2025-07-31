#!/bin/bash
# WiFi Network Switching Helper for tCam-Mini Development

echo "🔄 WiFi Network Switcher for tCam-Mini Development"
echo "=================================================="

# Function to connect to tCam-Mini AP
connect_tcam() {
    echo "📡 Connecting to tCam-Mini AP..."
    
    # Disconnect from current network
    nmcli device disconnect wlo1 2>/dev/null
    
    # Scan for networks
    echo "🔍 Scanning for tCam-Mini network..."
    nmcli device wifi rescan
    sleep 2
    
    # Look for tCam-Mini network
    if nmcli device wifi list | grep -q "tCam-Mini-CDE9"; then
        echo "✅ Found tCam-Mini-CDE9 network"
        
        # Connect to tCam-Mini AP (open network)
        nmcli device wifi connect "tCam-Mini-CDE9" ifname wlo1
        
        if [ $? -eq 0 ]; then
            echo "✅ Connected to tCam-Mini AP!"
            echo "📍 tCam-Mini IP: 192.168.4.1"
            
            # Test connectivity
            if ping -c 1 192.168.4.1 > /dev/null 2>&1; then
                echo "✅ tCam-Mini is reachable!"
            else
                echo "⚠️  Connected but cannot ping tCam-Mini"
            fi
        else
            echo "❌ Failed to connect to tCam-Mini AP"
        fi
    else
        echo "❌ tCam-Mini-CDE9 network not found"
        echo "   Please check:"
        echo "   1. tCam-Mini is powered on"
        echo "   2. tCam-Mini is in AP mode"
        echo "   3. You are within WiFi range"
    fi
}

# Function to connect back to home network
connect_home() {
    echo "🏠 Connecting to home network..."
    
    # Disconnect from current network
    nmcli device disconnect wlo1 2>/dev/null
    
    # Connect to home network
    nmcli device wifi connect "BT-X6F962" ifname wlo1
    
    if [ $? -eq 0 ]; then
        echo "✅ Connected to home network!"
        
        # Show IP address
        IP=$(ip addr show wlo1 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
        echo "📍 Your IP: $IP"
    else
        echo "❌ Failed to connect to home network"
    fi
}

# Function to show current status
show_status() {
    echo "📊 Current WiFi Status:"
    echo "----------------------"
    
    # Get current connection
    CURRENT=$(nmcli -t -f active,ssid dev wifi | grep "^yes" | cut -d: -f2)
    
    if [ -n "$CURRENT" ]; then
        echo "📡 Connected to: $CURRENT"
        
        # Show IP address
        IP=$(ip addr show wlo1 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
        echo "📍 IP Address: $IP"
        
        # Check if it's tCam network
        if [[ "$CURRENT" == "tCam-Mini-CDE9" ]]; then
            echo "🎯 Ready for tCam-Mini development!"
            echo "   tCam-Mini API: http://192.168.4.1/"
        fi
    else
        echo "❌ Not connected to any WiFi network"
    fi
}

# Main menu
case "$1" in
    tcam)
        connect_tcam
        ;;
    home)
        connect_home
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {tcam|home|status}"
        echo ""
        echo "Commands:"
        echo "  tcam    - Connect to tCam-Mini AP for development"
        echo "  home    - Connect back to home network"
        echo "  status  - Show current WiFi connection status"
        echo ""
        show_status
        ;;
esac
