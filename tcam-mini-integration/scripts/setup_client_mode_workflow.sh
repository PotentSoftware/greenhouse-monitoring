#!/bin/bash
# Complete workflow to configure tCam-Mini for WiFi client mode
# This eliminates the connectivity issues when working with the device

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🎯 tCam-Mini Client Mode Setup Workflow"
echo "========================================"
echo
echo "This workflow will:"
echo "1. Connect to tCam-Mini AP mode"
echo "2. Configure it for WiFi client mode"
echo "3. Wait for device reboot"
echo "4. Find device on home network"
echo "5. Test communication"
echo

# Check if WiFi password is configured
if grep -q "your_wifi_password_here" "$SCRIPT_DIR/configure_client_mode.py"; then
    echo "❌ ERROR: WiFi password not configured!"
    echo
    echo "Please edit the file:"
    echo "  $SCRIPT_DIR/configure_client_mode.py"
    echo
    echo "And set your WiFi password in the HOME_WIFI_PASSWORD variable."
    echo
    exit 1
else
    echo "✅ WiFi password appears to be configured"
fi

echo "📋 Current WiFi status:"
nmcli dev status | grep wifi
echo

read -p "🤔 Ready to start? This will temporarily disconnect from home WiFi. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 1
fi

echo
echo "🔄 Step 1: Connecting to tCam-Mini AP..."
echo "========================================"

# Connect to tCam-Mini AP
if ! "$SCRIPT_DIR/connect_tcam_simple.sh"; then
    echo "❌ Failed to connect to tCam-Mini AP"
    echo "💡 Make sure:"
    echo "   - tCam-Mini is powered on"
    echo "   - Device is in AP mode (default after firmware flash)"
    echo "   - You can see 'tCam-Mini-CDE9' in WiFi networks"
    exit 1
fi

echo
echo "⏱️  Waiting 5 seconds for network to stabilize..."
sleep 5

echo
echo "⚙️  Step 2: Configuring client mode..."
echo "========================================"

# Configure client mode
if python3 "$SCRIPT_DIR/configure_client_mode.py"; then
    echo "✅ Configuration sent successfully!"
else
    echo "❌ Configuration failed!"
    echo "💡 Check the error messages above"
    exit 1
fi

echo
echo "🔄 Step 3: Reconnecting to home WiFi..."
echo "========================================"

# Reconnect to home WiFi
echo "📡 Disconnecting from tCam-Mini AP..."
sudo nmcli device disconnect wlo1 2>/dev/null || true
sleep 2

echo "🏠 Reconnecting to home WiFi..."
# Try to reconnect to BT-X6F962 (your home WiFi)
if nmcli connection up "BT-X6F962" 2>/dev/null; then
    echo "✅ Reconnected to home WiFi"
else
    echo "⚠️  Automatic reconnection failed, trying manual connection..."
    if nmcli device wifi connect "BT-X6F962"; then
        echo "✅ Connected to home WiFi"
    else
        echo "❌ Failed to reconnect to home WiFi"
        echo "💡 Please manually reconnect to your home WiFi"
        echo "   The tCam-Mini should still be configuring itself"
    fi
fi

echo
echo "⏱️  Step 4: Waiting for tCam-Mini reboot and WiFi connection..."
echo "=============================================================="
echo "The tCam-Mini needs time to:"
echo "- Reboot with new configuration"
echo "- Connect to your home WiFi"
echo "- Start the socket server"
echo

for i in {30..1}; do
    echo -ne "\r⏰ Waiting ${i} seconds for device to reboot and connect..."
    sleep 1
done
echo -e "\r✅ Wait complete!                                              "

echo
echo "🔍 Step 5: Finding tCam-Mini on home network..."
echo "==============================================="

# Find the device on home network
if python3 "$SCRIPT_DIR/find_tcam_client.py"; then
    echo
    echo "🎉 SUCCESS! tCam-Mini is now in client mode!"
    echo "============================================"
    echo
    echo "✅ Benefits achieved:"
    echo "   - Both laptop and tCam-Mini on same network"
    echo "   - No more internet connectivity loss"
    echo "   - Ready for development and testing"
    echo
    echo "📍 Next steps:"
    echo "   1. Note the IP address found above"
    echo "   2. Update your test scripts with the new IP"
    echo "   3. Test the socket communication"
    echo "   4. Add HTTP server functionality"
    echo "   5. Implement /lepton3.5 endpoint"
    echo
else
    echo
    echo "⚠️  Device discovery incomplete"
    echo "==============================="
    echo
    echo "The configuration was sent, but the device wasn't found yet."
    echo "This could mean:"
    echo "   - Device is still rebooting (try waiting longer)"
    echo "   - WiFi credentials were incorrect"
    echo "   - Device reverted to AP mode due to connection failure"
    echo
    echo "💡 Troubleshooting:"
    echo "   1. Wait a few more minutes and run: python3 scripts/find_tcam_client.py"
    echo "   2. Check if tCam-Mini AP reappeared (indicates WiFi connection failed)"
    echo "   3. Verify WiFi credentials in configure_client_mode.py"
    echo
fi

echo
echo "🔧 Workflow complete!"
echo "====================="
