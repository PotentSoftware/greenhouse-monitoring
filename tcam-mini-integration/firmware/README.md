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
