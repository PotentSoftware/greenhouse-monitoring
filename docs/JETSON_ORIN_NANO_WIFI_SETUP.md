# Jetson Orin Nano Intel AX200NGW WiFi 6 Setup Guide

## Overview

This guide documents the complete setup process for installing and configuring the Intel AX200NGW WiFi 6 card on a Jetson Orin Nano running Ubuntu 22.04.5 LTS with the Tegra kernel (5.15.148-tegra).

## Hardware Information

- **Device**: NVIDIA Jetson Orin Nano
- **WiFi Card**: Intel AX200NGW WiFi 6 (M.2 2230 Key E)
- **Operating System**: Ubuntu 22.04.5 LTS (Jammy Jellyfish)
- **Kernel**: 5.15.148-tegra
- **Architecture**: ARM64

## Prerequisites

- Jetson Orin Nano with 2TB NVMe SSD
- Intel AX200NGW WiFi 6 card physically installed
- USB connection to development machine for initial setup
- Internet connectivity (via USB or Ethernet) for package downloads

## Hardware Detection Verification

First, verify that the Intel AX200NGW card is detected by the system:

```bash
# Check PCI devices for Intel WiFi card
lspci | grep -i intel
# Expected output: 0001:01:00.0 Network controller: Intel Corporation Wi-Fi 6 AX200 (rev 1a)

# Check if WiFi interface exists (initially should be empty)
ip link show | grep -E 'wl|wifi'
```

## Driver Installation Process

### Step 1: Update Package Lists

```bash
sudo apt update
```

### Step 2: Install Development Tools

```bash
sudo apt install -y dkms git make gcc
```

### Step 3: Install Intel WiFi Firmware

```bash
sudo apt install -y linux-firmware
```

### Step 4: Install Intel WiFi Drivers via DKMS

The key component is the `backport-iwlwifi-dkms` package, which provides Intel WiFi drivers compiled for the Jetson's Tegra kernel:

```bash
sudo apt install -y backport-iwlwifi-dkms
```

**Important**: This package will automatically:
- Download Intel WiFi driver source code
- Compile drivers specifically for the 5.15.148-tegra kernel
- Install the following modules:
  - `iwlwifi-compat.ko`
  - `iwlwifi.ko`
  - `iwlxvt.ko`
  - `iwlmvm.ko`
  - `mac80211.ko`
  - `cfg80211.ko`

### Step 5: Load the WiFi Driver

```bash
sudo modprobe iwlwifi
```

### Step 6: Verify WiFi Interface Creation

```bash
ip link show
# Look for interface like: wlP1p1s0
```

## WiFi Interface Configuration

### Bring Up the WiFi Interface

```bash
sudo ip link set wlP1p1s0 up
```

### Verify Interface Information

```bash
iw dev wlP1p1s0 info
```

Expected output should show:
- Interface type: managed
- MAC address
- Wiphy information

### Scan for Available Networks

```bash
sudo iw dev wlP1p1s0 scan | grep -E 'SSID|signal'
```

## Network Connection

### Connect to WiFi Network using NetworkManager

```bash
sudo nmcli device wifi connect 'NETWORK_NAME' password 'NETWORK_PASSWORD'
```

### Verify Connection

```bash
# Check IP address assignment
ip addr show wlP1p1s0

# Test internet connectivity
ping -c 3 8.8.8.8
```

## Firmware Files Location

The Intel AX200NGW firmware files are located at:
```
/lib/firmware/iwlwifi-cc-a0-*.ucode
```

Available firmware versions:
- iwlwifi-cc-a0-46.ucode through iwlwifi-cc-a0-77.ucode

## Troubleshooting

### Common Issues and Solutions

1. **Driver Not Loading**
   ```bash
   # Check if driver is loaded
   lsmod | grep iwl
   
   # If not loaded, try manual loading
   sudo modprobe iwlwifi
   ```

2. **Interface Not Appearing**
   ```bash
   # Check dmesg for errors
   dmesg | grep iwl
   
   # Restart NetworkManager
   sudo systemctl restart NetworkManager
   ```

3. **Connection Issues**
   ```bash
   # Check NetworkManager status
   nmcli device status
   
   # Reset WiFi interface
   sudo ip link set wlP1p1s0 down
   sudo ip link set wlP1p1s0 up
   ```

### Verification Commands

```bash
# Hardware detection
lspci | grep -i intel

# Driver status
lsmod | grep iwl

# Interface status
ip link show wlP1p1s0
iw dev wlP1p1s0 info

# Connection status
nmcli device wifi list
nmcli connection show

# Network connectivity
ping -c 3 8.8.8.8
```

## Performance Information

### WiFi 6 Capabilities

The Intel AX200NGW supports:
- **WiFi Standards**: 802.11ax (WiFi 6), backward compatible with 802.11ac/n/g/b
- **Frequency Bands**: 2.4 GHz and 5 GHz
- **Maximum Speed**: Up to 2.4 Gbps
- **MIMO**: 2x2 MU-MIMO
- **Security**: WPA3, WPA2

### Test Results

- **Signal Strength**: -45 dBm (excellent for home network)
- **Internet Latency**: ~14ms to Google DNS (8.8.8.8)
- **Connection Stability**: Stable, persistent across reboots

## Network Integration

### IP Address Assignment

The Jetson will receive an IP address via DHCP. In our setup:
- **WiFi IP**: 192.168.1.75
- **USB Backup IP**: 192.168.55.1

### Integration with Existing Network

The Jetson is now part of the same network as other greenhouse monitoring devices:
- **BeaglePlay**: 192.168.1.203 (precision sensors)
- **Feather S3[D]**: 192.168.1.81 (dual sensors)
- **tCam-Mini**: 192.168.1.130 (thermal camera)
- **Jetson Orin Nano**: 192.168.1.75 (AI processing)

## Persistent Configuration

### Auto-Connect on Boot

The WiFi connection is automatically saved and will reconnect on boot. To verify:

```bash
nmcli connection show
```

### Driver Loading on Boot

The `backport-iwlwifi-dkms` package ensures drivers are automatically loaded on boot through the kernel module system.

## SSH Access

### WiFi Access
```bash
ssh lionel@192.168.1.75
# Password: 357843
```

### USB Backup Access
```bash
ssh lionel@192.168.55.1
# Password: 357843
```

## Security Considerations

1. **WPA3 Support**: The Intel AX200NGW supports the latest WPA3 security standard
2. **MAC Address**: b0:a4:60:6b:74:d4 (can be randomized if needed)
3. **Network Isolation**: Consider VLAN setup for IoT device isolation

## Maintenance

### Driver Updates

The DKMS system will automatically rebuild drivers when the kernel is updated:

```bash
# Check DKMS status
sudo dkms status

# Manually rebuild if needed
sudo dkms build backport-iwlwifi/11510
sudo dkms install backport-iwlwifi/11510
```

### Firmware Updates

Firmware updates come through the `linux-firmware` package:

```bash
sudo apt update && sudo apt upgrade linux-firmware
```

## Conclusion

The Intel AX200NGW WiFi 6 card is now fully operational on the Jetson Orin Nano, providing high-performance wireless connectivity for greenhouse monitoring applications. The setup is persistent and will automatically reconnect on boot.

## Technical Specifications Summary

- **Interface Name**: wlP1p1s0
- **MAC Address**: b0:a4:60:6b:74:d4
- **Driver Package**: backport-iwlwifi-dkms (version 11510-0ubuntu1~22.04.3)
- **Kernel Modules**: iwlwifi, iwlmvm, mac80211, cfg80211
- **Firmware**: iwlwifi-cc-a0-*.ucode (multiple versions available)
- **Network Manager**: nmcli/NetworkManager
- **Connection Method**: WPA2/WPA3 with DHCP

---

**Setup Date**: August 16, 2025  
**Tested By**: Greenhouse Monitoring Project  
**Status**: Production Ready ✅
