# 🚀 Quick Reference - Greenhouse Monitoring

## Daily Commands

```bash
# Check if everything is running
./greenhouse_control.sh status

# Start monitoring in background  
./greenhouse_control.sh background

# Open all dashboards
./greenhouse_control.sh open

# View recent activity
./greenhouse_control.sh logs
```

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| 🌡️ **ESP32-S3 Thermal** | http://192.168.1.176 | None |
| 📊 **BeaglePlay Dashboard** | http://192.168.1.203:8081 | None |
| 📊 **Grafana Dashboard** | http://localhost:3000 | admin/admin |
| 🔧 **Node-RED Editor** | http://localhost:1880 | None |
| 💾 **InfluxDB Admin** | http://localhost:8086 | Token-based |

## 🔧 Quick Fixes

### Nothing is running
```bash
./greenhouse_control.sh background
```

### ESP32-S3 not responding  
```bash
./test_thermal_camera.sh
ping 192.168.1.176
```

### Need to restart everything
```bash
./greenhouse_control.sh stop
./greenhouse_control.sh background
```

### Check what's using resources
```bash
./greenhouse_control.sh status
htop  # See CPU/memory usage
```

## 📊 Key Metrics

- **Thermal Updates**: Every 5 seconds from ESP32-S3
- **Data Retention**: Unlimited (local storage)
- **Service Checks**: Every 30 seconds
- **ESP32-S3 Monitoring**: Every 5 minutes

## 🚨 Alert Conditions

**Automatic Recovery For:**
- InfluxDB service crashes
- Grafana service crashes  
- Node-RED process failures
- Telegraf collection stops

**Manual Check Required:**
- ESP32-S3 network disconnection
- BeaglePlay sensor failures
- Disk space issues

## 📁 Important Locations

```bash
# Control scripts
/home/lio/github/integration/infrastructure/

# System logs  
/home/lio/github/integration/infrastructure/logs/

# Node-RED flows
/home/lio/github/integration/node-red-flows/

# BeaglePlay code
/home/lio/github/integration/beagleplay_code/
```

## 💡 Pro Tips

1. **Background Mode**: Always use `background` for persistent monitoring
2. **Status First**: Check `status` before starting new services  
3. **Logs Help**: Use `logs` to troubleshoot issues
4. **Open All**: Use `open` to quickly access all interfaces
5. **ESP32-S3 IP**: Bookmark http://192.168.1.176 for quick thermal view

## 🔄 Update Frequency

- **Check Status**: As needed
- **View Logs**: Weekly or when troubleshooting  
- **Restart Services**: Only if status shows issues
- **System Maintenance**: Monthly review of logs and storage