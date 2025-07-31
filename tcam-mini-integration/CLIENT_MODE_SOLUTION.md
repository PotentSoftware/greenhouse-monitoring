# tCam-Mini WiFi Client Mode Solution

## Problem Solved
The tCam-Mini firmware runs in Access Point (AP) mode by default, creating its own WiFi network. This causes connectivity issues during development because:
- Connecting to tCam-Mini AP drops internet connection
- Can't maintain communication with development tools
- Requires constant WiFi switching

## Solution Overview
Configure the tCam-Mini to run in **WiFi Client Mode** instead of AP mode. This allows both your laptop and the tCam-Mini to connect to the same home WiFi network simultaneously.

## Key Discovery
The existing firmware already supports client mode! The decision is controlled by the `NET_INFO_FLAG_CLIENT_MODE` flag (0x80) in the network configuration. The firmware includes `set_wifi` and `get_wifi` commands that can modify this configuration.

## Implementation

### 1. Configuration Scripts Created

#### `scripts/configure_client_mode.py`
- Connects to tCam-Mini in AP mode
- Sends `set_wifi` command with client mode flags
- Configures home WiFi credentials
- **IMPORTANT**: Edit this file to set your WiFi password

#### `scripts/find_tcam_client.py`
- Discovers tCam-Mini on home network after configuration
- Uses multiple discovery methods (mDNS, network scan, ARP)
- Confirms device identity by testing socket communication

#### `scripts/setup_client_mode_workflow.sh`
- Complete automated workflow
- Handles WiFi switching, configuration, and discovery
- Provides step-by-step guidance and error handling

### 2. Network Configuration Details

**Current (AP Mode):**
- Device creates WiFi network "tCam-Mini-CDE9"
- IP: 192.168.4.1:5001
- Socket server on port 5001
- JSON commands over TCP

**After Client Mode:**
- Device connects to home WiFi (BT-X6F962)
- Gets DHCP IP on home network
- Same socket server on port 5001
- Same JSON command interface

### 3. Configuration Flags

```c
// From net_utilities.h
#define NET_INFO_FLAG_STARTUP_ENABLE 0x01
#define NET_INFO_FLAG_CLIENT_MODE    0x80

// Client mode configuration
flags = NET_INFO_FLAG_STARTUP_ENABLE | NET_INFO_FLAG_CLIENT_MODE;
```

## Usage Instructions

### Step 1: Configure WiFi Credentials
```bash
# Edit the configuration script
nano scripts/configure_client_mode.py

# Set your WiFi password
HOME_WIFI_PASSWORD = "your_actual_wifi_password"
```

### Step 2: Run Complete Workflow
```bash
# Execute the automated workflow
./scripts/setup_client_mode_workflow.sh
```

### Step 3: Find Device on Network
```bash
# If needed, manually search for device
python3 scripts/find_tcam_client.py
```

## Benefits Achieved

1. **Persistent Connectivity**: Both laptop and tCam-Mini on same network
2. **No Internet Loss**: Maintain development environment connectivity
3. **Production Ready**: Client mode is more suitable for deployment
4. **Easier Integration**: Standard network communication patterns
5. **mDNS Discovery**: Device advertises itself as `_tcam-socket._tcp`

## Next Steps

With client mode working, you can now:

1. **Test Socket Communication**: Use existing JSON commands
2. **Add HTTP Server**: Implement REST API alongside socket server
3. **Create /lepton3.5 Endpoint**: Custom endpoint for greenhouse monitoring
4. **Integrate with BeaglePlay**: Standard network communication
5. **Production Deployment**: Device connects to greenhouse WiFi

## Technical Notes

### Socket Server Details
- **Port**: 5001 (CMD_PORT in system_config.h)
- **Protocol**: TCP with JSON commands
- **mDNS**: Advertises as "_tcam-socket._tcp"
- **Commands**: get_status, get_wifi, set_wifi, etc.

### WiFi Configuration Structure
```json
{
  "cmd": "set_wifi",
  "sta_ssid": "BT-X6F962",
  "sta_pw": "password",
  "flags": 129  // 0x01 | 0x80 = STARTUP_ENABLE | CLIENT_MODE
}
```

### Discovery Methods
1. **mDNS**: `avahi-browse -t _tcam-socket._tcp -r`
2. **Port Scan**: Check port 5001 on network range
3. **ARP Table**: Look for ESP32 MAC address patterns

## Troubleshooting

### Device Not Found After Configuration
- Wait longer (device needs time to reboot and connect)
- Check WiFi credentials in configuration script
- Look for tCam-Mini AP reappearing (indicates connection failure)
- Run discovery script manually

### Configuration Fails
- Ensure connected to tCam-Mini AP first
- Check device is responding on 192.168.4.1:5001
- Verify socket connection works in AP mode

### Can't Connect to AP Mode
- Power cycle the tCam-Mini device
- Check for "tCam-Mini-CDE9" in available networks
- Ensure firmware is properly flashed

## Success Indicators

✅ Device connects to home WiFi automatically on boot
✅ Socket server accessible on home network IP
✅ mDNS service advertises device
✅ JSON commands work over network
✅ No more WiFi switching required for development

This solution eliminates the major connectivity barrier and enables seamless development of the HTTP server and greenhouse integration features.
