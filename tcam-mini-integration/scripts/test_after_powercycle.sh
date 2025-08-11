#!/bin/bash
echo "🔍 Testing tCam-Mini after power cycle..."
echo "========================================"

echo "1. Testing ping connectivity..."
ping -c 3 192.168.1.130

echo -e "\n2. Testing port 5001 (socket API)..."
nmap -p 5001 192.168.1.130

echo -e "\n3. Testing thermal image capture..."
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts
python3 quick_thermal_view.py

echo -e "\n4. If successful, the thermal viewer will automatically switch to live mode!"
