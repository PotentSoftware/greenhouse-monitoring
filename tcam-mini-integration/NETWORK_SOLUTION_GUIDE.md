# tCam-Mini Network Solution Guide

## Problem
Your tCam-Mini currently runs in AP (Access Point) mode, creating its own WiFi network "tCam-Mini-CDE9". When you connect to it, you lose internet connectivity because your laptop switches from your home WiFi to the tCam's network.

## Solution
Configure the tCam-Mini to run in **Station Mode** so it connects to your home WiFi network instead of creating its own AP. This allows both your laptop and tCam-Mini to be on the same network simultaneously.

## Step-by-Step Process

### Step 1: Flash Station Mode Configurator

1. **Connect tCam-Mini via USB**
   ```bash
   # Check connection
   lsusb | grep "CP210x"
   ls -la /dev/ttyUSB0
   ```

2. **Flash the configurator**
   ```bash
   cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware
   ./flash_station_mode.sh
   ```

3. **Watch the configuration process**
   - The script will open a serial monitor
   - You should see messages like:
     ```
     === tCam-Mini Station Mode Configurator ===
     Configuring for station mode...
     ✅ Station mode configuration complete!
     Configuration:
       WiFi SSID: BT-X6F962
       Client mode: ENABLED
     ```

### Step 2: Flash Normal Firmware

After the configurator runs and restarts the device:

```bash
./flash_precompiled.sh
```

### Step 3: Find Your tCam-Mini on the Network

```bash
cd ../scripts
python3 find_tcam_on_network.py
```

This will scan your home network (192.168.1.x) and find devices with tCam ports open.

## Expected Results

✅ **Before (AP Mode):**
- tCam creates "tCam-Mini-CDE9" network
- You must connect to it, losing internet
- Access at: 192.168.4.1:5001

✅ **After (Station Mode):**
- tCam connects to "BT-X6F962" (your home WiFi)
- You stay connected to home WiFi
- Access at: 192.168.1.XXX:5001 (discovered by scanner)
- Both devices on same network = no internet loss!

## Configuration Details

The station mode configurator sets:
- **WiFi SSID**: BT-X6F962 (your home network)
- **WiFi Password**: N7nCfV3RE6d4Ra
- **Client Mode**: Enabled
- **DHCP**: Enabled (automatic IP assignment)

## Troubleshooting

### If tCam-Mini not found on network:

1. **Check serial output during boot:**
   ```bash
   python -m serial.tools.miniterm /dev/ttyUSB0 115200
   ```
   Look for WiFi connection messages.

2. **Verify configuration:**
   - Check if station mode configurator ran successfully
   - Verify WiFi credentials in `station_mode_config/main/main.c`

3. **Reset to AP mode if needed:**
   - Connect to tCam-Mini-CDE9 AP
   - Use tCam desktop app to reset network settings
   - Re-run station mode configuration

### If connection issues persist:

1. **Check WiFi signal strength** at tCam location
2. **Verify router settings** (MAC filtering, etc.)
3. **Try manual IP assignment** instead of DHCP

## Alternative Solutions

### Option 1: WiFi Bridge/Repeater
- Use a WiFi repeater to bridge tCam AP to home network
- More complex but doesn't require firmware changes

### Option 2: Jetson Nano as Bridge
- When your Jetson Nano arrives, it could act as a bridge
- Connect to tCam AP via one WiFi adapter
- Connect to home network via ethernet or second WiFi
- Run proxy/bridge software

### Option 3: Custom Firmware with Dual Mode
- Modify tCam firmware to support both AP and Station modes
- Switch between modes via web interface or button press

## Benefits of Station Mode Solution

✅ **Simple**: Uses existing tools and configuration  
✅ **Clean**: No additional hardware required  
✅ **Reliable**: Direct connection to home network  
✅ **Scalable**: Can add multiple tCam devices easily  
✅ **Future-proof**: Works with Jetson Nano when it arrives  

## Integration with Jetson Nano

Once your Jetson Nano arrives:
1. tCam-Mini will already be on home network
2. Jetson can connect to same network
3. Direct communication without network switching
4. Can run more advanced thermal processing on Jetson
5. BeaglePlay integration still possible

This solution gives you the best of both worlds: working thermal camera access AND maintained internet connectivity!
