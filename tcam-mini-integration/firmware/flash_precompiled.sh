#!/bin/bash
# Flash precompiled tCam-Mini firmware

set -e

echo "🔥 Flashing Precompiled tCam-Mini Firmware"
echo "=========================================="

# Check if environment is set up
if [ -z "$IDF_PATH" ]; then
    echo "⚠️  ESP-IDF environment not loaded. Loading..."
    source setup_env.sh
fi

cd tcam-firmware

echo "📡 Ready to flash PRECOMPILED firmware to tCam-Mini..."
echo "⚠️  Make sure tCam-Mini is connected via USB"
echo "📍 Expected device: /dev/ttyUSB0"

# Check if USB device exists
if [ -e "/dev/ttyUSB0" ]; then
    echo "✅ USB device found: /dev/ttyUSB0"
    read -p "Press Enter to continue with flashing precompiled firmware, or Ctrl+C to cancel..."
    
    echo "📡 Flashing precompiled firmware..."
    python -m esptool --chip esp32 -b 460800 --before default_reset --after hard_reset write_flash \
        --flash_mode dio --flash_size 8MB --flash_freq 80m \
        0x1000 precompiled/bootloader.bin \
        0x8000 precompiled/partition-table.bin \
        0xd000 precompiled/ota_data_initial.bin \
        0x10000 precompiled/tCamMini.bin
    
    echo ""
    echo "✅ Precompiled firmware flashed successfully!"
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
    echo "  python -m esptool --chip esp32 -b 460800 --before default_reset --after hard_reset write_flash \\"
    echo "    --flash_mode dio --flash_size 8MB --flash_freq 80m \\"
    echo "    0x1000 precompiled/bootloader.bin \\"
    echo "    0x8000 precompiled/partition-table.bin \\"
    echo "    0xd000 precompiled/ota_data_initial.bin \\"
    echo "    0x10000 precompiled/tCamMini.bin"
fi
