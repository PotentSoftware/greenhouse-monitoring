# Getting Started with tCam-Mini-Rev 4

## Immediate First Steps

### 1. Hardware Setup
Since your tCam-Mini is already connected to the USB hub and powered up, let's verify it's working:

```bash
# Check if tCam-Mini is detected as USB device
lsusb | grep -i "cp210x\|silicon\|tcam"

# Check for tCam-Mini network interface (if WiFi is configured)
ping 192.168.1.xxx  # Replace with tCam-Mini IP if known
```

### 2. Install tCam Desktop Software

Download the tCam desktop application from:
- **Linux**: https://github.com/danjulio/tCam/releases
- **Documentation**: https://danjuliodesigns.com/products/tcam_mini.html

```bash
# Download latest release (adjust version as needed)
wget https://github.com/danjulio/tCam/releases/download/vX.X.X/tCam_linux.tar.gz
tar -xzf tCam_linux.tar.gz
cd tCam_linux
./tCam
```

### 3. Initial Testing Checklist

**USB Connection Test**:
- [ ] tCam-Mini powers up (LED indicators)
- [ ] Desktop software detects camera
- [ ] Can capture thermal images
- [ ] Radiometric mode works (temperature data per pixel)

**Basic Functionality Test**:
- [ ] Image quality is good
- [ ] Temperature readings are realistic
- [ ] Can save images with temperature data
- [ ] Camera settings can be adjusted

**Greenhouse Test**:
- [ ] Point camera at greenhouse plants
- [ ] Capture thermal images of leaves
- [ ] Verify temperature differences between leaves and background
- [ ] Document optimal camera distance and angle

### 4. API Discovery

Once basic functionality is confirmed, we need to understand the tCam-Mini HTTP API:

```bash
# If tCam-Mini has WiFi configured, test HTTP endpoints
curl http://[TCAM_IP]/status
curl http://[TCAM_IP]/camera
curl http://[TCAM_IP]/image
```

Common tCam-Mini API endpoints (to be verified):
- `/status` - Camera status and configuration
- `/image` - Current thermal image
- `/stream` - Streaming thermal data
- `/config` - Camera configuration

## Development Environment Setup

### 1. Create Development Directory Structure

```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/
mkdir -p {scripts,test_images,docs,cv_development}
```

### 2. Install Required Python Libraries

```bash
# On your development machine
pip install opencv-python numpy scipy scikit-image requests pillow matplotlib

# Later, install same packages on BeaglePlay
ssh debian@192.168.1.203
pip install opencv-python numpy scipy scikit-image requests pillow matplotlib
```

### 3. Create Initial Test Scripts

I'll create some basic scripts to get you started with tCam-Mini communication and image processing.

## What to Document

As you test the tCam-Mini, please document:

1. **Hardware Observations**:
   - LED behavior during startup
   - Power consumption
   - Physical mounting considerations

2. **Software Capabilities**:
   - Available API endpoints
   - Image formats and resolutions
   - Temperature data format
   - Configuration options

3. **Image Quality**:
   - Temperature accuracy
   - Image clarity
   - Optimal camera settings for greenhouse use
   - Distance and angle recommendations

4. **Network Configuration**:
   - WiFi setup process
   - IP address assignment
   - Network performance

This information will be crucial for the next phases of development.

## Troubleshooting

### Common Issues

**tCam-Mini not detected**:
- Check USB connection
- Verify power supply
- Try different USB port
- Check for driver issues

**Desktop software won't connect**:
- Verify tCam-Mini is powered
- Check USB cable
- Try restarting tCam-Mini
- Check for conflicting software

**Poor image quality**:
- Adjust camera settings
- Check lens for obstructions
- Verify proper distance to subject
- Ensure stable mounting

**Network connectivity issues**:
- Verify WiFi configuration
- Check network settings
- Test with different network
- Use USB connection as fallback

## Next Steps

Once you have the tCam-Mini producing images:

1. **Document the API** - We need to understand exactly how to get thermal images and temperature data
2. **Test with greenhouse plants** - Capture sample images for computer vision development
3. **Set up BeaglePlay communication** - Establish reliable data transfer
4. **Begin computer vision development** - Start working on leaf identification algorithms

The key is to start simple and build up complexity gradually. Getting basic thermal imaging working is the essential first step before we can add the advanced leaf analysis features.