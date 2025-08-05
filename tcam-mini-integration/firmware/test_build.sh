#!/bin/bash
# Quick test build without flashing

set -e

# Check if environment is set up
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  ESP-IDF environment not loaded. Run: source setup_env.sh"
    exit 1
fi

cd tcam-firmware

echo "🔨 Testing build of tCam-Mini firmware..."
idf.py build

echo "✅ Build successful! Ready for modifications."
