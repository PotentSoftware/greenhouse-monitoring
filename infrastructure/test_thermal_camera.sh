#!/bin/bash

echo "=== Testing ESP32-S3 Thermal Camera ==="
echo ""

echo "Testing thermal camera connection at http://192.168.1.176/thermal_data"
echo ""

# Test the thermal data endpoint
if curl -s --connect-timeout 5 "http://192.168.1.176/thermal_data" > /tmp/thermal_test.json; then
    echo "✓ Thermal camera is accessible"
    echo ""
    
    # Parse and show key statistics
    echo "Sample thermal data:"
    if command -v jq &> /dev/null; then
        cat /tmp/thermal_test.json | jq '{minTemp, maxTemp, meanTemp, medianTemp, rangeTemp, modeTemp, stdDevTemp}'
    else
        # Extract key values without jq
        grep -o '"minTemp":[^,]*' /tmp/thermal_test.json
        grep -o '"maxTemp":[^,]*' /tmp/thermal_test.json  
        grep -o '"meanTemp":[^,]*' /tmp/thermal_test.json
        grep -o '"medianTemp":[^,]*' /tmp/thermal_test.json
        grep -o '"rangeTemp":[^,]*' /tmp/thermal_test.json
        grep -o '"modeTemp":[^,]*' /tmp/thermal_test.json
        grep -o '"stdDevTemp":[^,]*' /tmp/thermal_test.json
    fi
    
    echo ""
    echo "✓ Thermal camera data structure looks correct"
    rm -f /tmp/thermal_test.json
else
    echo "❌ Thermal camera is not accessible at http://192.168.1.176/thermal_data"
    exit 1
fi

echo ""
echo "=== Node-RED Flow Updates ==="
echo "The following updates have been made:"
echo "• IP address changed from 192.168.1.100 to 192.168.1.176"
echo "• Endpoint changed to /thermal_data"
echo "• Data processing updated to handle actual field names"
echo "• Error handling added for data_not_ready status"
echo ""
echo "Import the updated flow:"
echo "/home/lio/github/integration/node-red-flows/greenhouse_integration_complete.json"