#!/bin/bash
# Build and flash tCam-Mini firmware

set -e

# Check if environment is set up
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  ESP-IDF environment not loaded. Run: source setup_env.sh"
    exit 1
fi

cd tcam-firmware

echo "🔨 Building tCam-Mini firmware..."
idf.py build

echo ""
echo "📡 Ready to flash firmware to tCam-Mini..."
echo "⚠️  Make sure tCam-Mini is connected via USB"
echo "📍 Expected device: /dev/ttyUSB0"

# Check if USB device exists
if [ -e "/dev/ttyUSB0" ]; then
    echo "✅ USB device found: /dev/ttyUSB0"
    read -p "Press Enter to continue with flashing, or Ctrl+C to cancel..."
    
    echo "📡 Flashing firmware..."
    idf.py -p /dev/ttyUSB0 flash
    
    echo ""
    echo "✅ Firmware flashed successfully!"
    echo ""
    echo "📊 Opening serial monitor..."
    echo "Press Ctrl+] to exit monitor"
    idf.py -p /dev/ttyUSB0 monitor
else
    echo "❌ USB device /dev/ttyUSB0 not found"
    echo "Available USB devices:"
    ls -la /dev/ttyUSB* 2>/dev/null || echo "No USB devices found"
    echo ""
    echo "To flash manually:"
    echo "  idf.py -p /dev/ttyUSB0 flash"
    echo "  idf.py -p /dev/ttyUSB0 monitor"
fi
