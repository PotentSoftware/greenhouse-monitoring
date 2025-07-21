#!/bin/bash
# Script to install and configure the dark mode dashboard with timestamp header
# This script should be run on the BeaglePlay device

echo "Setting up dark mode dashboard with timestamp header for BeaglePlay..."

# Define paths
FLOW_PATH="/home/lio/github/greenhouse-monitoring/node-red-flows/greenhouse_dark_mode_flow.json"
NODE_RED_DIR="/home/debian/.node-red"
NODE_RED_FLOWS_FILE="${NODE_RED_DIR}/flows.json"
NODE_RED_SETTINGS_FILE="${NODE_RED_DIR}/settings.js"

# Check if Node-RED is installed
if ! command -v node-red &> /dev/null; then
    echo "Error: Node-RED is not installed. Please install Node-RED first."
    exit 1
fi

# Check if the flow file exists
if [ ! -f "$FLOW_PATH" ]; then
    echo "Error: Flow file not found at $FLOW_PATH"
    exit 1
fi

# Backup existing flows
echo "Backing up existing Node-RED flows..."
if [ -f "$NODE_RED_FLOWS_FILE" ]; then
    cp "$NODE_RED_FLOWS_FILE" "${NODE_RED_FLOWS_FILE}.backup.$(date +%Y%m%d%H%M%S)"
fi

# Import the new flow
echo "Importing dark mode dashboard flow..."
# We need to merge the new flow with existing flows
if [ -f "$NODE_RED_FLOWS_FILE" ]; then
    # Extract existing flows (excluding the tab definition)
    EXISTING_FLOWS=$(cat "$NODE_RED_FLOWS_FILE" | grep -v '"type": "tab"' | grep -v '"id": "greenhouse_dark_mode"')
    
    # Combine with new flow
    echo "[" > "$NODE_RED_FLOWS_FILE.tmp"
    cat "$FLOW_PATH" | sed '1s/\[//' | sed '$s/\]/,/' >> "$NODE_RED_FLOWS_FILE.tmp"
    echo "$EXISTING_FLOWS" >> "$NODE_RED_FLOWS_FILE.tmp"
    echo "]" >> "$NODE_RED_FLOWS_FILE.tmp"
    
    # Replace the flows file
    mv "$NODE_RED_FLOWS_FILE.tmp" "$NODE_RED_FLOWS_FILE"
else
    # If no existing flows, just use the new flow
    cp "$FLOW_PATH" "$NODE_RED_FLOWS_FILE"
fi

# Update Node-RED settings to enable UI dark theme if not already enabled
if [ -f "$NODE_RED_SETTINGS_FILE" ]; then
    echo "Configuring Node-RED settings for dark theme..."
    
    # Check if ui settings already exist
    if grep -q "ui:" "$NODE_RED_SETTINGS_FILE"; then
        # Update existing ui settings
        sed -i 's/theme: "theme-light"/theme: "theme-dark"/' "$NODE_RED_SETTINGS_FILE"
    else
        # Add ui settings before the closing module.exports
        sed -i '/module.exports = {/a\    ui: { theme: "theme-dark" },' "$NODE_RED_SETTINGS_FILE"
    fi
fi

# Restart Node-RED to apply changes
echo "Restarting Node-RED service..."
systemctl restart node-red || sudo systemctl restart node-red

echo "Waiting for Node-RED to start..."
sleep 10

echo "Setup complete!"
echo "Your BeaglePlay dashboard now has:"
echo "✓ Dark mode theme"
echo "✓ Landscape layout"
echo "✓ Timestamp header showing data acquisition time"
echo ""
echo "Access the dashboard at http://192.168.1.203:1880/ui"
echo "Note: The URL may change if the BeaglePlay is disconnected from the laptop."
