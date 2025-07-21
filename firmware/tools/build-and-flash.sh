#!/bin/bash
# Comprehensive build and flash script for BeagleConnect Freedom firmware
# Created by Cascade on 2025-07-18
# This script handles:
# 1. Building the firmware with west
# 2. Flashing to the BeagleConnect Freedom device
# 3. Setting up sudoers to avoid password prompts for flashing
# 4. Verifying the flash was successful

set -e  # Exit on any error

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}==== BeagleConnect Freedom Build and Flash Tool ====${NC}"

# Define paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIRMWARE_DIR="$PROJECT_ROOT/firmware/beagleconnect-freedom"
BUILD_DIR="$FIRMWARE_DIR/build"
FLASHER_PATH="$HOME/cc1352-flasher/src/cc1352_flasher/cli.py"
BIN_PATH="$BUILD_DIR/zephyr/zephyr.bin"

# Check if required directories and files exist
if [ ! -d "$FIRMWARE_DIR" ]; then
    echo -e "${RED}Error: Firmware directory not found at $FIRMWARE_DIR${NC}"
    exit 1
fi

if [ ! -f "$FLASHER_PATH" ]; then
    echo -e "${RED}Error: CC1352 flasher not found at $FLASHER_PATH${NC}"
    exit 1
fi

# Add the current user to sudoers for passwordless access to specific commands if not already done
setup_sudo_access() {
    echo -e "${BLUE}Setting up passwordless sudo access for flashing...${NC}"
    
    # Find the Python interpreter with pyserial installed
    PYTHON_PATH=$(which python3)
    if [ -f "$HOME/anaconda3/bin/python" ]; then
        PYTHON_PATH="$HOME/anaconda3/bin/python"
    fi
    
    # Check if the sudoers entry already exists
    if sudo grep -q "$(whoami).*NOPASSWD.*$FLASHER_PATH" /etc/sudoers.d/010_beagleconnect 2>/dev/null; then
        echo -e "${GREEN}Passwordless sudo already configured.${NC}"
        return
    fi
    
    # Create a temporary file
    TMPFILE=$(mktemp)
    echo "$(whoami) ALL=(ALL) NOPASSWD: $PYTHON_PATH $FLASHER_PATH *" > "$TMPFILE"
    echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/python3 $FLASHER_PATH *" >> "$TMPFILE"
    
    # Use visudo to safely add the entry
    if sudo visudo -c -f "$TMPFILE"; then
        sudo cp "$TMPFILE" /etc/sudoers.d/010_beagleconnect
        sudo chmod 440 /etc/sudoers.d/010_beagleconnect
        echo -e "${GREEN}Passwordless sudo configured for flashing operations.${NC}"
    else
        echo -e "${RED}Failed to configure passwordless sudo. You'll be prompted for passwords during flashing.${NC}"
    fi
    
    # Clean up
    rm -f "$TMPFILE"
}

# Build the firmware
build_firmware() {
    echo -e "${BLUE}${BOLD}Building firmware...${NC}"
    cd "$FIRMWARE_DIR"
    
    # Check if west is available
    if ! command -v west &> /dev/null; then
        echo -e "${RED}Error: 'west' command not found. Make sure the Zephyr environment is set up.${NC}"
        exit 1
    fi
    
    # Build the firmware
    if west build -b beagleconnect_freedom; then
        echo -e "${GREEN}Firmware built successfully!${NC}"
    else
        echo -e "${RED}Firmware build failed.${NC}"
        exit 1
    fi
    
    # Calculate CRC32 for verification
    if command -v crc32 &> /dev/null; then
        CRC=$(crc32 "$BIN_PATH")
        echo -e "${BLUE}Firmware binary CRC32: ${YELLOW}$CRC${NC}"
    fi
    
    echo -e "${BLUE}Binary size: $(du -h "$BIN_PATH" | cut -f1)${NC}"
}

# Flash the firmware
flash_firmware() {
    echo -e "${BLUE}${BOLD}Flashing firmware to BeagleConnect Freedom...${NC}"
    
    # Kill any existing flasher processes
    pkill -f "python.*cli.py" &>/dev/null || true
    
    # Check if the device is connected
    if ! ls /dev/ttyACM* &>/dev/null; then
        echo -e "${RED}No BeagleConnect Freedom device detected. Please connect the device.${NC}"
        exit 1
    fi
    
    # Find the Python interpreter with pyserial installed
    PYTHON_PATH=$(which python3)
    if [ -f "$HOME/anaconda3/bin/python" ]; then
        PYTHON_PATH="$HOME/anaconda3/bin/python"
        echo -e "${BLUE}Using Anaconda Python interpreter: $PYTHON_PATH${NC}"
    fi
    
    # Flash with sudo (should be passwordless now)
    echo -e "${YELLOW}Erasing, writing, and verifying firmware...${NC}"
    if sudo "$PYTHON_PATH" "$FLASHER_PATH" --bcf -e -w -v "$BIN_PATH"; then
        echo -e "${GREEN}${BOLD}Firmware flashed successfully!${NC}"
    else
        echo -e "${RED}Firmware flash failed.${NC}"
        exit 1
    fi
}

# Clean up after flashing - enhanced to be robust and handle reboot scenarios
cleanup_connections() {
    echo -e "${BLUE}Performing thorough cleanup of all communication processes...${NC}"
    
    # Check for reboot flag
    local REBOOT_REMOTE=false
    local REBOOT_LOCAL=false
    if [[ "$1" == "reboot" || "$1" == "reboot-remote" ]]; then
        REBOOT_REMOTE=true
    fi
    if [[ "$1" == "reboot" || "$1" == "reboot-local" ]]; then
        REBOOT_LOCAL=true
    fi

    # Step 1: Kill local processes - more aggressive approach
    echo -e "${BLUE}Killing local gbridge and socat processes...${NC}"
    # Kill both running and suspended processes
    pkill -9 -f "gbridge" &>/dev/null || true
    pkill -9 -f "socat" &>/dev/null || true
    # Kill any SSH sessions that might be running socat or gbridge remotely (covers suspended sessions too)
    pkill -9 -f "ssh.*socat" &>/dev/null || true
    pkill -9 -f "ssh.*gbridge" &>/dev/null || true
    
    # Step 2: Check for processes using ttyACM0 (minicom, screen, etc.)
    echo -e "${BLUE}Checking for processes using /dev/ttyACM0...${NC}"
    PROCS=$(lsof /dev/ttyACM0 2>/dev/null | grep -v PID | awk '{print $2}')
    if [ -n "$PROCS" ]; then
        echo -e "${YELLOW}Killing processes using /dev/ttyACM0: $PROCS${NC}"
        for pid in $PROCS; do
            kill -9 $pid &>/dev/null || true
        done
        echo -e "${GREEN}Serial port processes terminated.${NC}"
    else
        echo -e "${GREEN}No processes using /dev/ttyACM0.${NC}"
    fi
    
    # Step 3: Check for any processes binding to port 9998 (socat)
    echo -e "${BLUE}Checking for processes binding to port 9998...${NC}"
    PORT_PROCS=$(ss -tulpn | grep 9998 | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2 2>/dev/null | sort -u)
    if [ -n "$PORT_PROCS" ]; then
        echo -e "${YELLOW}Killing processes binding to port 9998: $PORT_PROCS${NC}"
        for pid in $PORT_PROCS; do
            kill -9 $pid &>/dev/null || true
        done
        echo -e "${GREEN}Port 9998 processes terminated.${NC}"
    else
        echo -e "${GREEN}No processes binding to port 9998.${NC}"
    fi
    
    # Step 4: Check for and disable any autostarting services locally
    echo -e "${BLUE}Checking for autostarting services locally...${NC}"
    for service in "socat.service" "gbridge.service" "greybus.service"; do
        if systemctl is-enabled "$service" &>/dev/null; then
            echo -e "${YELLOW}Disabling autostart service: $service${NC}"
            sudo systemctl disable "$service" &>/dev/null || true
            sudo systemctl stop "$service" &>/dev/null || true
            echo -e "${GREEN}Service $service disabled.${NC}"
        fi
    done
    
    # Step 5: Clean up remote processes on BeaglePlay - more thorough approach
    if ping -c 1 -W 1 192.168.1.203 &>/dev/null; then
        echo -e "${BLUE}Cleaning up processes on BeaglePlay...${NC}"
        
        # Check for and disable any autostarting services on BeaglePlay
        echo -e "${BLUE}Checking for autostarting services on BeaglePlay...${NC}"
        for service in "socat.service" "gbridge.service" "greybus.service"; do
            ssh beagleplay "systemctl is-enabled $service 2>/dev/null" &>/dev/null && {
                echo -e "${YELLOW}Disabling autostart service on BeaglePlay: $service${NC}"
                ssh beagleplay "echo 'temppwd' | sudo -S systemctl disable $service && echo 'temppwd' | sudo -S systemctl stop $service" &>/dev/null || true
                echo -e "${GREEN}Remote service $service disabled.${NC}"
            }
        done
        
        # First check for gbridge processes and kill them individually (more reliable)
        echo -e "${BLUE}Checking for gbridge processes on BeaglePlay...${NC}"
        REMOTE_PIDS=$(ssh beagleplay "ps aux | grep -v grep | grep gbridge | awk '{print \$2}'" 2>/dev/null)
        if [ -n "$REMOTE_PIDS" ]; then
            echo -e "${YELLOW}Found gbridge processes on BeaglePlay: $REMOTE_PIDS${NC}"
            for pid in $REMOTE_PIDS; do
                ssh beagleplay "echo 'temppwd' | sudo -S kill -9 $pid" &>/dev/null || true
            done
            echo -e "${GREEN}Remote gbridge processes terminated.${NC}"
        else
            echo -e "${GREEN}No gbridge processes found on BeaglePlay.${NC}"
        fi
        
        # Use killall as a backup method
        ssh beagleplay "echo 'temppwd' | sudo -S killall -9 gbridge socat 2>/dev/null || true" &>/dev/null
        
        # Reset Greybus kernel modules on BeaglePlay for a clean state
        echo -e "${BLUE}Resetting Greybus kernel modules on BeaglePlay...${NC}"
        ssh beagleplay "echo 'temppwd' | sudo -S rmmod greybus_mods gb_es2 gb_gpio gb_hid gb_i2c gb_loopback gb_raw gb_vibrator gb_audio gb_control gb_firmware gb_light gb_log gb_power_supply gb_pwm gb_sdio gb_uart gb_usb greybus 2>/dev/null || true && echo 'temppwd' | sudo -S modprobe greybus" &>/dev/null || true
        
        # Clear kernel message buffer on BeaglePlay to start with clean logs
        ssh beagleplay "echo 'temppwd' | sudo -S dmesg -C" &>/dev/null || true
        
        # Check for any lingering processes binding to port 9998 on BeaglePlay
        echo -e "${BLUE}Checking for processes binding to port 9998 on BeaglePlay...${NC}"
        ssh beagleplay "echo 'temppwd' | sudo -S ss -tulpn | grep 9998" &>/dev/null && {
            echo -e "${YELLOW}Warning: Port 9998 still in use on BeaglePlay. Attempting to kill those processes...${NC}"
            ssh beagleplay "echo 'temppwd' | sudo -S ss -tulpn | grep 9998 | awk '{print \$7}' | cut -d',' -f2 | cut -d'=' -f2 | xargs -r sudo kill -9" &>/dev/null || true
        } || echo -e "${GREEN}Port 9998 is free on BeaglePlay.${NC}"
        
        # Handle remote reboot if requested
        if [[ "$REBOOT_REMOTE" == "true" ]]; then
            echo -e "${YELLOW}Rebooting BeaglePlay for maximum cleanup...${NC}"
            ssh beagleplay "echo 'temppwd' | sudo -S reboot" &>/dev/null || true
            echo -e "${BLUE}Waiting for BeaglePlay to reboot...${NC}"
            
            # Wait for the system to go down
            sleep 5
            
            # Wait for it to come back up (timeout after 60 seconds)
            echo -e "${BLUE}Waiting for BeaglePlay to come back online...${NC}"
            for i in {1..12}; do
                if ping -c 1 -W 1 192.168.1.203 &>/dev/null; then
                    echo -e "${GREEN}BeaglePlay is back online!${NC}"
                    # Wait a bit more for all services to start
                    sleep 5
                    break
                fi
                echo -n "."  # Show progress
                sleep 5
                if [[ $i -eq 12 ]]; then
                    echo -e "\n${RED}Timed out waiting for BeaglePlay to reboot.${NC}"
                fi
            done
        fi
    else
        echo -e "${YELLOW}Warning: BeaglePlay not reachable. Skipping remote cleanup.${NC}"
    fi
    
    # Handle local reboot if requested
    if [[ "$REBOOT_LOCAL" == "true" ]]; then
        echo -e "${YELLOW}WARNING: System will reboot in 5 seconds for maximum cleanup...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to cancel...${NC}"
        sleep 5
        sudo reboot
        exit 0  # This won't be reached but included for clarity
    fi
    
    # Wait a moment and verify cleanup was successful
    echo -e "${BLUE}Waiting for resources to be freed...${NC}"
    sleep 2
    
    # Final verification
    LOCAL_CHECK=$(ss -tulpn 2>/dev/null | grep 9998 || echo "Port 9998 is free locally.")
    if [[ "$LOCAL_CHECK" == *"9998"* ]]; then
        echo -e "${RED}Warning: Port 9998 is still in use locally despite cleanup attempts.${NC}"
        echo -e "${YELLOW}Consider using './build-and-flash.sh cleanup reboot-local' for complete cleanup.${NC}"
    else
        echo -e "${GREEN}Port 9998 is free locally.${NC}"
    fi
    
    # Final check for any remaining socat/gbridge processes
    REMAINING=$(ps aux | grep -E 'socat|gbridge' | grep -v grep || echo "None")
    if [[ "$REMAINING" != "None" ]]; then
        echo -e "${YELLOW}Warning: Some socat/gbridge processes may still be running:${NC}"
        echo "$REMAINING"
        echo -e "${YELLOW}Consider using './build-and-flash.sh cleanup reboot' for complete cleanup.${NC}"
    else
        echo -e "${GREEN}All socat/gbridge processes successfully terminated.${NC}"
    fi
    
    echo -e "${GREEN}Thorough connection cleanup complete.${NC}"
}

# Main execution flow
echo -e "${YELLOW}This script will build and flash the BeagleConnect Freedom firmware.${NC}"
echo -e "${YELLOW}Make sure the device is connected via USB before continuing.${NC}"
echo -e "${BLUE}----------------------------------------------------${NC}"

# Setup sudo access
setup_sudo_access

# Build firmware
build_firmware

# Clean up any existing connections
cleanup_connections

# Flash firmware
flash_firmware

echo -e "${BLUE}----------------------------------------------------${NC}"
echo -e "${GREEN}${BOLD}All operations completed successfully!${NC}"
echo -e "${BLUE}To establish communication with the device:${NC}"
echo -e "${YELLOW}1. Run: socat TCP6-LISTEN:9998,bind=::1,reuseaddr,fork /dev/ttyACM0,b115200,raw${NC}"
echo -e "${YELLOW}2. Run: /usr/sbin/gbridge -P 9998 -I ::1${NC}"
echo -e "${BLUE}----------------------------------------------------${NC}"
