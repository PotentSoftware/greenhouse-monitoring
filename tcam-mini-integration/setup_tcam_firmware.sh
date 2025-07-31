#!/bin/bash
# tCam-Mini Firmware Setup (using existing ESP-IDF)

set -e  # Exit on any error

echo "🚀 tCam-Mini Firmware Setup"
echo "============================"

# Use existing ESP-IDF installation
ESP_IDF_PATH="/home/lio/github/esp/esp-idf"
FIRMWARE_DIR="/home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware"

echo "📍 Using existing ESP-IDF: $ESP_IDF_PATH"

# Verify ESP-IDF exists
if [ ! -d "$ESP_IDF_PATH" ]; then
    echo "❌ ESP-IDF not found at $ESP_IDF_PATH"
    exit 1
fi

# Create firmware development directory
echo "📁 Creating firmware directory: $FIRMWARE_DIR"
mkdir -p "$FIRMWARE_DIR"
cd "$FIRMWARE_DIR"

# Clone tCam-Mini source code
echo ""
echo "📥 Cloning tCam-Mini source code..."
if [ ! -d "tcam-mini-source" ]; then
    git clone https://github.com/danjulio/lepton.git tcam-mini-source
    echo "   ✅ tCam-Mini source cloned"
else
    echo "   tCam-Mini source already exists, updating..."
    cd tcam-mini-source
    git pull
    cd ..
fi

# Copy ESP32 firmware to working directory
echo ""
echo "📋 Setting up tCam-Mini ESP32 firmware..."
if [ ! -d "tcam-firmware" ]; then
    cp -r tcam-mini-source/ESP32 tcam-firmware
    echo "   ✅ Firmware copied to working directory"
else
    echo "   Firmware working directory already exists"
fi

# Create environment setup script
echo ""
echo "📝 Creating environment setup script..."
cat > setup_env.sh << EOF
#!/bin/bash
# Source this script to set up ESP-IDF environment
# Usage: source setup_env.sh

export IDF_PATH="$ESP_IDF_PATH"

# Source ESP-IDF environment
if [ -f "\$IDF_PATH/export.sh" ]; then
    source "\$IDF_PATH/export.sh"
    echo "✅ ESP-IDF environment loaded"
    echo "📍 IDF_PATH: \$IDF_PATH"
    echo "🔧 Available commands: idf.py, esptool.py"
else
    echo "❌ ESP-IDF not found at \$IDF_PATH"
    exit 1
fi
EOF

chmod +x setup_env.sh

# Create build and flash script
echo ""
echo "📝 Creating build and flash script..."
cat > build_and_flash.sh << 'EOF'
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
EOF

chmod +x build_and_flash.sh

# Create quick test script
echo ""
echo "📝 Creating quick test script..."
cat > test_build.sh << 'EOF'
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
EOF

chmod +x test_build.sh

# Create development guide
echo ""
echo "📝 Creating development guide..."
cat > README.md << 'EOF'
# tCam-Mini Custom Firmware Development

## Quick Start

### 1. Set up environment (once per terminal session)
```bash
source setup_env.sh
```

### 2. Test build (recommended first step)
```bash
./test_build.sh
```

### 3. Build and flash firmware
```bash
./build_and_flash.sh
```

## Project Structure

```
tcam-firmware/
├── main/
│   ├── app_main.c          # Main application
│   ├── cmd_task.c          # Command processing
│   ├── wifi_task.c         # WiFi management
│   ├── lepton_task.c       # Thermal camera interface
│   ├── system_config.h     # Configuration
│   └── ...
├── components/             # ESP-IDF components
└── CMakeLists.txt         # Build configuration
```

## Development Goals

1. **Add HTTP Server in Client Mode**
   - Currently only available in AP mode
   - Need to start HTTP server when connected to home WiFi

2. **Add Greenhouse API Endpoints**
   - `/api/thermal_data` - Raw thermal data
   - `/api/leaf_analysis` - Processed leaf data
   - `/api/status` - Device status

3. **Optimize for BeaglePlay Integration**
   - Efficient data formats
   - Reliable communication
   - Error handling

## Key Files to Modify

- `main/wifi_task.c` - Add HTTP server startup in client mode
- `main/app_main.c` - Main application logic
- `main/system_config.h` - Add configuration options

## Build Commands

```bash
# Full build
cd tcam-firmware && idf.py build

# Clean build
cd tcam-firmware && idf.py fullclean && idf.py build

# Flash only
cd tcam-firmware && idf.py -p /dev/ttyUSB0 flash

# Monitor serial output
cd tcam-firmware && idf.py -p /dev/ttyUSB0 monitor
```

## Next Steps

1. Test build with existing firmware
2. Analyze current HTTP server implementation
3. Modify to enable server in client mode
4. Add greenhouse-specific endpoints
5. Test with BeaglePlay integration
EOF

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "📁 Firmware development directory: $FIRMWARE_DIR"
echo "📍 Using ESP-IDF: $ESP_IDF_PATH"
echo ""
echo "🚀 Next Steps:"
echo "1. cd $FIRMWARE_DIR"
echo "2. source setup_env.sh"
echo "3. ./test_build.sh        # Test compilation first"
echo "4. ./build_and_flash.sh   # Build and flash to device"
echo ""
echo "📖 Read README.md for detailed instructions"
