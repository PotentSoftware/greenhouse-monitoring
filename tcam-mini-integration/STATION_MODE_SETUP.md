# tCam-Mini Station Mode Setup Guide

This guide explains how to configure your tCam-Mini to connect to your home WiFi network instead of creating its own access point.

## Current Status
✅ **I2C Communication Fixed** - Lepton camera detection working  
✅ **WiFi AP Working** - Device creates "tCam-Mini-CDE9" at 192.168.4.1  
❌ **Station Mode** - Device not connected to home network  

## Why Station Mode?
- **Same Network Access**: Both laptop and tCam-Mini on your home WiFi
- **No Network Switching**: Maintain remote access while testing
- **Easier Integration**: Direct access to thermal viewer and web interface
- **Better Workflow**: No need to disconnect from home network

## Option 1: Web Interface Configuration (Recommended)

### Step 1: Connect to tCam-Mini WiFi
```bash
# Temporarily connect to tCam-Mini network
nmcli device wifi connect "tCam-Mini-CDE9"
```

### Step 2: Access Web Interface
- Open browser to: http://192.168.4.1
- Navigate to Network/WiFi settings
- Configure station mode with your home WiFi credentials

### Step 3: Reconnect to Home Network
```bash
# Reconnect to home WiFi
nmcli connection up "BT-X6F962"
```

## Option 2: Firmware Configuration Tool

### Step 1: Build Station Mode Configurator
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware/station_mode_config

# Source ESP-IDF environment
source /home/lio/github/esp/esp-idf/export.sh

# Set target
idf.py set-target esp32

# Configure WiFi credentials in main/main.c (line 85):
# strcpy(net_info.sta_pw, "your_actual_wifi_password");

# Build
idf.py build

# Flash
idf.py -p /dev/ttyUSB0 flash monitor
```

### Step 2: Flash Back Normal Firmware
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware/tcam-firmware
idf.py -p /dev/ttyUSB0 flash
```

## Option 3: Manual NVS Configuration

### Using ESP32 NVS Partition Tool
```bash
# Create NVS CSV with WiFi config
# Flash NVS partition directly
```

## Expected Results

### After Station Mode Configuration:
1. **Device Boot**: tCam-Mini connects to "BT-X6F962" WiFi
2. **IP Assignment**: Device gets IP from your router (likely 192.168.1.x)
3. **Network Discovery**: Find device IP using:
   ```bash
   nmap -sn 192.168.1.0/24 | grep -B2 "34:86:5d:09:cd:e8"
   ```
4. **Thermal Viewer**: Run with new IP:
   ```bash
   python3 tcam_thermal_viewer.py --host <device_ip>
   ```
5. **Web Interface**: Access at http://<device_ip>/

## Network Configuration Details

### Current AP Mode Settings:
- **SSID**: tCam-Mini-CDE9
- **IP**: 192.168.4.1
- **Mode**: Access Point
- **Flag**: 0x01 (AP mode)

### Target Station Mode Settings:
- **SSID**: BT-X6F962 (your home WiFi)
- **Password**: [Your WiFi password]
- **IP**: DHCP assigned (192.168.1.x)
- **Flag**: 0x81 (Client mode + Startup enable)

## Troubleshooting

### If Station Mode Fails:
1. **Check WiFi Credentials**: Ensure SSID and password are correct
2. **Signal Strength**: Move device closer to router
3. **Revert to AP Mode**: Flash configurator with AP mode settings
4. **Serial Monitor**: Check connection logs via `idf.py monitor`

### If Device Not Found on Network:
```bash
# Scan for device MAC address
sudo nmap -sn 192.168.1.0/24
arp -a | grep 34:86:5d

# Check router admin panel for connected devices
```

## Next Steps After Station Mode

1. **Test Thermal Viewer**: 
   ```bash
   python3 tcam_thermal_viewer.py --host <device_ip>
   ```

2. **Test Web Interface**:
   ```bash
   curl http://<device_ip>/
   ```

3. **Integrate with Greenhouse System**:
   - Add thermal camera endpoint to BeaglePlay dashboard
   - Configure thermal data collection
   - Set up automated thermal monitoring

## Security Notes

- **WiFi Password**: Store securely, don't commit to git
- **Network Access**: Device will be accessible from entire home network
- **Firewall**: Consider router firewall rules if needed

## Files Created

- `station_mode_config/` - Standalone configuration utility
- `STATION_MODE_SETUP.md` - This guide
- `test_tcam_connection.py` - Network connectivity tester

Choose **Option 1** (Web Interface) for the easiest approach, or **Option 2** (Firmware Tool) for more control.
