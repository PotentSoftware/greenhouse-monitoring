#!/bin/bash
# Source this script to set up ESP-IDF environment
# Usage: source setup_env.sh

export IDF_PATH="/home/lio/github/esp/esp-idf"

# Source ESP-IDF environment
if [ -f "$IDF_PATH/export.sh" ]; then
    source "$IDF_PATH/export.sh"
    echo "✅ ESP-IDF environment loaded"
    echo "📍 IDF_PATH: $IDF_PATH"
    echo "🔧 Available commands: idf.py, esptool.py"
else
    echo "❌ ESP-IDF not found at $IDF_PATH"
    exit 1
fi
