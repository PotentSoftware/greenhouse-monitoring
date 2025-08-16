# Jetson Orin Nano WiFi Quick Reference

## 🚀 Quick Commands

### Connection Status
```bash
# Check WiFi interface
ip addr show wlP1p1s0

# Check connection
nmcli device status

# Test internet
ping -c 3 8.8.8.8
```

### Troubleshooting
```bash
# Restart WiFi
sudo ip link set wlP1p1s0 down && sudo ip link set wlP1p1s0 up

# Reload driver
sudo modprobe -r iwlwifi && sudo modprobe iwlwifi

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

### Network Information
- **WiFi IP**: 192.168.1.75
- **USB Backup**: 192.168.55.1
- **Interface**: wlP1p1s0
- **MAC**: b0:a4:60:6b:74:d4

### SSH Access
```bash
# WiFi (primary)
ssh lionel@192.168.1.75

# USB (backup)
ssh lionel@192.168.55.1
```

### Network Scan
```bash
# Scan for networks
sudo iw dev wlP1p1s0 scan | grep SSID

# Connect to new network
sudo nmcli device wifi connect 'SSID' password 'PASSWORD'
```

## 🔧 Hardware Details

- **Card**: Intel AX200NGW WiFi 6
- **Driver**: backport-iwlwifi-dkms
- **Kernel**: 5.15.148-tegra
- **Status**: ✅ Production Ready

## 🌐 Network Integration

| Device | IP Address | Purpose |
|--------|------------|---------|
| Jetson Orin Nano | 192.168.1.75 | AI Processing |
| BeaglePlay | 192.168.1.203 | Precision Sensors |
| Feather S3[D] | 192.168.1.81 | Dual Sensors |
| tCam-Mini | 192.168.1.130 | Thermal Camera |
