#!/bin/bash
# Flash Station Mode Configurator to tCam-Mini

set -e

echo "🔧 tCam-Mini Station Mode Configurator"
echo "======================================"
echo ""
echo "This will configure your tCam-Mini to connect to your home WiFi"
echo "network instead of creating its own access point."
echo ""
echo "WiFi Network: BT-X6F962"
echo "Device: /dev/ttyUSB0"
echo ""

# Check if USB device exists
if [ ! -e "/dev/ttyUSB0" ]; then
    echo "❌ USB device /dev/ttyUSB0 not found"
    echo "Available devices:"
    ls -la /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "No USB devices found"
    exit 1
fi

echo "✅ USB device found: /dev/ttyUSB0"
echo ""

# Check if environment is set up
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  ESP-IDF environment not loaded. Loading..."
    source setup_env.sh
fi

echo "📡 Ready to flash station mode configurator..."
read -p "Press Enter to continue, or Ctrl+C to cancel..."

echo ""
echo "🔥 Flashing station mode configurator..."

# Flash the station mode configurator
esptool --chip esp32 -b 460800 --before default_reset --after hard_reset write_flash \
    --flash_mode dio --flash_size 8MB --flash_freq 80m \
    0x1000 station_mode_config/build/bootloader/bootloader.bin \
    0x8000 station_mode_config/build/partition_table/partition-table.bin \
    0x10000 station_mode_config/build/tcam_station_config.bin

echo ""
echo "✅ Station mode configurator flashed successfully!"
echo ""
echo "📊 Opening serial monitor to watch configuration..."
echo "The device will configure WiFi settings and restart automatically."
echo "Press Ctrl+] to exit monitor"
echo ""

# Monitor the configuration process
python3 -m serial.tools.miniterm /dev/ttyUSB0 115200

echo ""
echo "🎯 Next steps:"
echo "1. The device should have configured WiFi settings"
echo "2. Flash back the normal tCam firmware: ./flash_precompiled.sh"
echo "3. The tCam-Mini will then connect to your home WiFi network"
echo "4. You can find it on your network and access it without losing internet!"
