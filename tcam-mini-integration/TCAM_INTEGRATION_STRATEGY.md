# tCam-Mini Integration Strategy

## Current Status ✅

- **tCam-Mini Location**: 192.168.1.246 (ESP_4A6CA4)
- **WiFi Configuration**: Successfully joined home network (BT-X6F962)
- **AP Mode**: Available as tCam-Mini-CDE9 (192.168.4.1)
- **Console App**: Working when connected to AP mode

## Communication Protocol Analysis

### Access Point Mode (192.168.4.1)
- ✅ HTTP server active
- ✅ JSON API endpoints available
- ✅ tCam Console app works
- ✅ Suitable for development and testing

### Client Mode (192.168.1.246)
- ❌ No HTTP server
- ❌ No open ports
- ❌ Cannot be accessed as server
- ❌ Designed for outbound connections only

## Integration Options

### Option 1: AP Mode Development (Immediate)
**Advantages:**
- Works with existing firmware
- Full API access available
- No firmware modifications needed
- Can start development immediately

**Implementation:**
1. Connect BeaglePlay to tCam-Mini AP network
2. Access thermal data via HTTP API at 192.168.4.1
3. Develop leaf detection algorithms
4. Test thermal image processing

**Limitations:**
- BeaglePlay loses internet access when connected to tCam-Mini
- Not suitable for production deployment
- Manual network switching required

### Option 2: Custom Firmware (Recommended)
**Advantages:**
- Full control over communication protocol
- Can add HTTP server in client mode
- Optimized for greenhouse integration
- Production-ready solution

**Implementation:**
1. Clone tCam-Mini firmware from GitHub
2. Modify to add HTTP server in client mode
3. Add greenhouse-specific API endpoints
4. Flash custom firmware to tCam-Mini

**Requirements:**
- ESP-IDF development environment
- Firmware compilation and flashing
- Custom API development

### Option 3: Push-Based Integration (Advanced)
**Advantages:**
- tCam-Mini pushes data to BeaglePlay
- No polling required
- Real-time data streaming
- Efficient bandwidth usage

**Implementation:**
1. Modify tCam-Mini firmware to push data
2. Configure BeaglePlay as data receiver
3. Implement webhook/HTTP POST endpoints
4. Add thermal data processing pipeline

## Recommended Implementation Plan

### Phase 1: AP Mode Development (Week 1)
1. **Connect BeaglePlay to tCam-Mini AP**
2. **Discover and document API endpoints**
3. **Capture thermal images and data**
4. **Develop leaf detection algorithms**
5. **Test temperature analysis functions**

### Phase 2: Firmware Analysis (Week 2)
1. **Clone and study tCam-Mini source code**
2. **Set up ESP-IDF development environment**
3. **Compile and test existing firmware**
4. **Identify modification points for HTTP server**

### Phase 3: Custom Firmware Development (Week 3-4)
1. **Add HTTP server to client mode**
2. **Implement greenhouse-specific API endpoints**
3. **Add leaf analysis integration hooks**
4. **Test custom firmware thoroughly**

### Phase 4: Production Integration (Week 5)
1. **Deploy custom firmware to tCam-Mini**
2. **Integrate with BeaglePlay monitoring system**
3. **Add thermal data to dashboard**
4. **Implement enhanced VPD calculations**

## Technical Requirements

### Development Environment
- ESP-IDF framework
- Python 3.x for scripts
- OpenCV for image processing
- Git for version control

### Hardware Setup
- tCam-Mini Rev 4 with FLIR Lepton 3.5
- BeaglePlay for processing
- USB cable for firmware flashing
- WiFi network for communication

### Software Components
- Custom tCam-Mini firmware
- BeaglePlay integration scripts
- Thermal image processing pipeline
- Leaf detection algorithms
- Enhanced VPD calculations

## Next Steps

1. **Start with Option 1** (AP Mode) for immediate development
2. **Document all API endpoints** and data formats
3. **Develop thermal processing algorithms**
4. **Plan custom firmware modifications**
5. **Set up ESP-IDF development environment**

## Expected Outcomes

- **High-resolution thermal imaging** (160x120 vs 32x24)
- **Advanced leaf identification** and segmentation
- **Per-leaf temperature statistics** (6 measurements)
- **Enhanced VPD calculations** using leaf temperatures
- **Real-time thermal monitoring** integrated with dashboard
- **Production-ready greenhouse monitoring** system

## Success Criteria

- [ ] Thermal images captured from tCam-Mini
- [ ] Leaf detection algorithms working
- [ ] Per-leaf temperature analysis implemented
- [ ] Integration with BeaglePlay dashboard
- [ ] Enhanced VPD calculations active
- [ ] Production deployment completed
