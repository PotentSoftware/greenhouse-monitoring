#!/bin/bash

# Generate mock sensor data in InfluxDB line protocol format
# This simulates greenhouse sensors until real devices are connected

timestamp=$(date +%s)000000000

# Generate realistic sensor values (using awk for better compatibility)
ph=$(awk "BEGIN {printf \"%.2f\", 6.0 + (int(rand() * 200)) / 100}")
temp=$(awk "BEGIN {printf \"%.1f\", 22.0 + (int(rand() * 80)) / 10}")
humidity=$(awk "BEGIN {printf \"%.1f\", 50.0 + (int(rand() * 300)) / 10}")
canopy_temp=$(awk -v t="$temp" "BEGIN {printf \"%.1f\", t + (int(rand() * 40) - 20) / 10}")

# Calculate VPD
vpd=$(awk "BEGIN {printf \"%.3f\", 0.8 + (int(rand() * 800)) / 1000}")

# Output in InfluxDB line protocol format
echo "greenhouse_sensors,location=greenhouse,sensor=ph ph_value=${ph} ${timestamp}"
echo "greenhouse_sensors,location=greenhouse,sensor=temperature air_temp=${temp} ${timestamp}"
echo "greenhouse_sensors,location=greenhouse,sensor=humidity humidity=${humidity} ${timestamp}"
echo "greenhouse_sensors,location=greenhouse,sensor=thermal canopy_temp=${canopy_temp} ${timestamp}"
echo "greenhouse_sensors,location=greenhouse,sensor=vpd vpd_value=${vpd} ${timestamp}"
