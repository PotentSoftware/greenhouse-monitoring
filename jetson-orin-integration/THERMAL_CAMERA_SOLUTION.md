# Thermal Camera Integration Solution

## Current Situation

The tCam-Mini thermal camera (192.168.1.130) only runs its HTTP/socket server in AP mode, not in station mode. This is a firmware limitation that prevents direct access when the device is connected to your home WiFi network.

## Previous Working Setup

- **Development Laptop**: 192.168.1.223 running `tcam_web_interface.py` on port 8080
- **BeaglePlay Dashboard**: Directly linked to http://192.168.1.223:8080 for thermal data
- **Architecture**: The web interface acted as a bridge between tCam-Mini and HTTP clients

## Current Implementation

### Services Running on Jetson

1. **tCam Web Interface** (Primary)
   - Port: 8080
   - Script: `/tcam-mini-integration/scripts/tcam_web_interface.py`
   - Status: Running but cannot connect to tCam-Mini in station mode
   - Endpoints: `/thermal_raw`, `/thermal_image`, `/status`, `/device_info`

2. **tCam Proxy Server** (Fallback)
   - Port: 5002
   - Script: `/jetson-orin-integration/src/tcam_proxy_server.py`
   - Status: Provides simulated thermal data
   - Purpose: Ensures dashboard always has thermal data to display

3. **Streamlit Dashboard**
   - Port: 8501
   - Tries web interface first (localhost:8080), then falls back to proxy (localhost:5002)

## Solutions

### Option 1: Firmware Modification (Recommended)

Enable HTTP server in station mode by modifying the tCam-Mini firmware:

```bash
# Build environment already set up
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware
source setup_env.sh
cd tcam-firmware

# Key files to modify:
# - main/net_cmd_task.c (HTTP server logic)
# - components/sys/wifi_utilities.c (WiFi management)

# Build and flash
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

The firmware build environment is ready and tested. The modification would enable the HTTP server to run when connected as a WiFi client.

### Option 2: Network Bridge (Current Workaround)

Continue using the current setup with simulated data from the proxy server until firmware can be modified.

### Option 3: AP Mode Bridge (Disruptive)

Use `tcam_ap_bridge.py` to temporarily switch networks, but this causes connectivity interruptions.

## Quick Commands

```bash
# Start all services (includes web interface and proxy)
cd /home/lio/github/greenhouse-monitoring/jetson-orin-integration
./start_all_services.sh

# Check service status
curl http://localhost:8080/status    # Web interface
curl http://localhost:5002/status    # Proxy server
curl http://localhost:8501           # Streamlit dashboard

# View logs
tail -f /tmp/tcam_web_interface.log
tail -f /tmp/tcam_proxy.log
tail -f /tmp/streamlit.log
```

## Next Steps

1. **Immediate**: Continue using proxy server for simulated thermal data
2. **Short-term**: Modify tCam-Mini firmware to enable HTTP server in station mode
3. **Long-term**: Full integration with real thermal data from modified firmware

## Network Architecture

```
                    ┌─────────────────┐
                    │   Streamlit     │
                    │  Dashboard      │
                    │  (Port 8501)    │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
            ┌───────▼──────┐ ┌───────▼──────┐
            │ Web Interface│ │ Proxy Server │
            │ (Port 8080)  │ │ (Port 5002)  │
            │   PRIMARY    │ │   FALLBACK   │
            └───────┬──────┘ └───────┬──────┘
                    │                 │
                    X                 │
            (Connection Blocked)      │
                    │          (Simulated Data)
            ┌───────▼──────┐
            │  tCam-Mini   │
            │ 192.168.1.130│
            │ (Station Mode)│
            └──────────────┘
```

## Key Finding

The tCam-Mini firmware can be modified to enable the HTTP server in station mode. The build environment is ready and the specific files that need modification have been identified. This is the most sustainable solution for real thermal data integration.
