# Greenhouse Monitoring System - Troubleshooting Guide

**Last Updated**: 2025-08-11  
**System Version**: v2.0 (Feather S3[D] + tCam-Mini Integration)

## 🚨 Quick Diagnosis

### **System Status Check**
```bash
# Check all component connectivity
ping -c 3 192.168.1.203  # BeaglePlay
ping -c 3 192.168.1.81   # Feather S3[D]
ping -c 3 192.168.1.130  # tCam-Mini

# Check web interfaces
curl -I http://192.168.1.203:8081/  # Dashboard
curl -I http://192.168.1.81:8080/sensors  # Sensor data
curl -I http://192.168.1.223:8080/  # Thermal interface
```

## 🔧 Common Issues & Solutions

### **1. Sensor Data Showing Zeros**

**Symptoms:**
- Dashboard displays 0.0°C temperature
- 0.0% humidity readings
- "Feather S3[D]: disconnected" status

**Root Cause:**
- Feather S3[D] WiFi reconnection after power cycle
- ESP32 devices need 2-5 minutes to fully reconnect

**Solution:**
```bash
# Wait 5 minutes, then test connectivity
ping -c 3 192.168.1.81
curl http://192.168.1.81:8080/sensors
```

**Prevention:**
- Allow 5 minutes after any power events before troubleshooting
- Avoid unnecessary power cycles

### **2. Thermal Camera Not Loading**

**Symptoms:**
- Tools → Thermal Camera shows blank page
- Connection timeout errors
- No thermal images displayed

**Diagnosis:**
```bash
# Check tCam-Mini connectivity
ping -c 3 192.168.1.130
nmap -p 5001 192.168.1.130

# Check thermal interface
curl -I http://192.168.1.223:8080/
```

**Solutions:**
1. **tCam-Mini offline**: Power cycle tCam-Mini, wait 2 minutes
2. **Thermal interface down**: Restart thermal interface on laptop
3. **High latency**: Power cycle tCam-Mini if ping > 500ms

### **3. Dashboard Inaccessible**

**Symptoms:**
- http://192.168.1.203:8081/ not loading
- Connection refused errors
- Blank page or timeout

**Diagnosis:**
```bash
# Check BeaglePlay connectivity
ping -c 3 192.168.1.203

# Check if dashboard service is running
ssh debian@192.168.1.203 "ps aux | grep precision_sensors_server"
```

**Solutions:**
1. **BeaglePlay offline**: Check power and network connection
2. **Service crashed**: Restart dashboard service
3. **Port conflict**: Kill conflicting processes on port 8081

### **4. WiFi Reconnection Issues**

**Symptoms:**
- Devices not responding after power cycle
- Intermittent connectivity
- IP address changes

**Root Cause:**
- ESP32/CircuitPython WiFi stack initialization delay
- DHCP lease renewal timing
- Router DHCP table cleanup

**Solution Process:**
1. **Wait 5 minutes** - Most critical step
2. **Check network scan**: `nmap -sn 192.168.1.0/24`
3. **Power cycle if needed**: Only after 5-minute wait
4. **Verify WiFi credentials**: Check settings.toml on Feather S3[D]

## 🔍 Advanced Diagnostics

### **BeaglePlay Dashboard Service**

**Check service status:**
```bash
ssh debian@192.168.1.203 "ps aux | grep precision_sensors_server"
ssh debian@192.168.1.203 "netstat -tlnp | grep 8081"
```

**View logs:**
```bash
ssh debian@192.168.1.203 "tail -20 /home/debian/precision_server.log"
```

**Restart service:**
```bash
ssh debian@192.168.1.203 "pkill -f precision_sensors_server.py"
ssh debian@192.168.1.203 "cd /home/debian && nohup python3 precision_sensors_server.py > precision_server.log 2>&1 &"
```

### **Feather S3[D] Sensor Board**

**Check CircuitPython status:**
```bash
# If connected via USB
cat /dev/ttyACM0  # View serial output
```

**Test HTTP endpoint:**
```bash
curl http://192.168.1.81:8080/sensors | jq .
```

**Expected response:**
```json
{
  "timestamp": "2025-08-11T20:00:00",
  "sht45": {"temperature": 22.5, "humidity": 71.8},
  "hdc3022": {"temperature": 23.3, "humidity": 73.4},
  "averages": {"temperature": 22.9, "humidity": 72.6, "vpd": 0.77}
}
```

### **tCam-Mini Thermal Camera**

**Check socket connectivity:**
```bash
telnet 192.168.1.130 5001
```

**Test thermal image capture:**
```bash
cd tcam-mini-integration/scripts
python3 quick_thermal_view.py
```

**Check thermal interface logs:**
```bash
# If running on laptop
ps aux | grep tcam_web_interface
```

## 🚑 Emergency Recovery

### **Complete System Reset**

1. **Power cycle all devices:**
   - Unplug BeaglePlay (wait 10 seconds, reconnect)
   - Unplug Feather S3[D] power (wait 10 seconds, reconnect)
   - Unplug tCam-Mini power (wait 10 seconds, reconnect)

2. **Wait 5 minutes** for all WiFi reconnections

3. **Restart laptop thermal interface:**
   ```bash
   pkill -f tcam_web_interface
   cd tcam-mini-integration/scripts
   python3 tcam_web_interface.py --tcam-ip 192.168.1.130 --web-port 8080
   ```

4. **Verify all components:**
   ```bash
   ping -c 3 192.168.1.203 && echo "BeaglePlay OK"
   ping -c 3 192.168.1.81 && echo "Feather S3[D] OK"  
   ping -c 3 192.168.1.130 && echo "tCam-Mini OK"
   ```

### **Network Discovery**

**Find devices if IP addresses changed:**
```bash
# Scan for HTTP servers
nmap -p 8080,8081 192.168.1.0/24

# Scan for tCam-Mini
nmap -p 5001 192.168.1.0/24

# Look for device names
nmap -sn 192.168.1.0/24 | grep -E "(BeaglePlay|Feather|tCam)"
```

## 📊 Performance Monitoring

### **Normal Operating Parameters**

**Network Latency:**
- BeaglePlay: < 50ms
- Feather S3[D]: < 100ms  
- tCam-Mini: < 200ms (acceptable up to 500ms)

**Update Frequencies:**
- Sensor data: Every 5 seconds
- Dashboard refresh: Every 5 seconds
- Thermal images: Real-time streaming

**Memory Usage:**
- BeaglePlay: < 50% RAM utilization
- Feather S3[D]: > 8MB free memory reported

### **Warning Signs**

**Network Issues:**
- Ping latency > 1000ms consistently
- Frequent connection timeouts
- IP address conflicts

**Hardware Issues:**
- Sensor readings stuck at same values
- Thermal images showing artifacts
- Memory warnings in logs

## 🔄 Maintenance Schedule

### **Daily Checks**
- Verify dashboard accessibility
- Check for any error indicators

### **Weekly Checks**
- Review system logs for errors
- Verify all sensor readings are reasonable
- Test thermal camera functionality

### **Monthly Checks**
- Check SD card usage on BeaglePlay
- Verify data export functionality
- Review network performance

## 📞 Support Information

### **Log Locations**
- **BeaglePlay**: `/home/debian/precision_server.log`
- **Thermal Interface**: Console output or specified log file
- **Feather S3[D]**: Serial output via USB connection

### **Configuration Files**
- **BeaglePlay**: `/home/debian/precision_sensors_server.py`
- **Feather S3[D]**: `/media/*/CIRCUITPY/settings.toml`
- **Thermal Interface**: Command line arguments

### **Network Configuration**
- **WiFi Network**: BT-X6F962
- **IP Range**: 192.168.1.0/24
- **Gateway**: 192.168.1.254

---

**Remember**: Most issues resolve with patience - allow 5 minutes for WiFi reconnection after any power events before troubleshooting!
