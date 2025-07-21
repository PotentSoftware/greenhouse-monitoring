#!/bin/bash
# Script to configure HDMI display on BeaglePlay at 1920x1080 resolution
# This script should be run directly on the BeaglePlay device

echo "Setting up HDMI display at 1920x1080 resolution on BeaglePlay..."

# BeaglePlay uses TI AM62x SoC which has specific display configuration methods
# This script targets the specific hardware of the BeaglePlay

# Function to check if we're running on BeaglePlay
check_beagleplay() {
    if grep -q "BeaglePlay" /proc/device-tree/model 2>/dev/null || grep -q "AM62" /proc/device-tree/model 2>/dev/null; then
        echo "✓ Confirmed running on BeaglePlay device"
        return 0
    else
        echo "Warning: This doesn't appear to be a BeaglePlay device."
        echo "This script is designed specifically for the BeaglePlay."
        echo "Continue anyway? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to detect display using BeaglePlay-specific methods
detect_displays() {
    echo "Checking for connected displays..."
    
    # Check if we can see the display connector in sysfs
    if [ -d "/sys/class/drm/" ]; then
        echo "Display connectors found in sysfs:"
        ls -la /sys/class/drm/ | grep -E 'card|HDMI'
        
        # Look for HDMI specifically
        if ls -la /sys/class/drm/ | grep -q -i 'hdmi'; then
            echo "✓ HDMI connector detected in system"
            return 0
        fi
    fi
    
    # Alternative check for display devices
    if [ -d "/sys/devices/platform/display" ]; then
        echo "Display platform device found"
        return 0
    fi
    
    # Check if the splash screen is visible (indirect check)
    echo "Could not detect display through system interfaces."
    echo "Can you see the BeagleBoard.org splash screen or any output on the display? (y/n)"
    read -r display_visible
    if [[ "$display_visible" =~ ^[Yy]$ ]]; then
        echo "✓ Display confirmed working by user"
        return 0
    else
        echo "No display detected or confirmed."
        return 1
    fi
}

# Function to set resolution using standard Linux tools
set_resolution() {
    echo "Setting display resolution to 1920x1080..."
    
    # Try different methods depending on what's available
    
    # Method 1: Using xrandr if X is running
    if command -v xrandr &> /dev/null && [ -n "$DISPLAY" ]; then
        echo "Using xrandr to set resolution..."
        HDMI_OUTPUT=$(xrandr | grep "HDMI" | grep " connected" | cut -d " " -f1)
        
        if [ -n "$HDMI_OUTPUT" ]; then
            xrandr --output "$HDMI_OUTPUT" --mode 1920x1080
            if [ $? -eq 0 ]; then
                echo "Successfully set resolution using xrandr."
                return 0
            fi
        fi
    fi
    
    # Method 2: Using fbset for framebuffer
    if command -v fbset &> /dev/null; then
        echo "Using fbset to set framebuffer resolution..."
        fbset -xres 1920 -yres 1080
        if [ $? -eq 0 ]; then
            echo "Successfully set framebuffer resolution."
            return 0
        fi
    fi
    
    # Method 3: Using kernel boot parameters (requires reboot)
    echo "Adding kernel boot parameters for resolution..."
    if [ -d "/boot/firmware" ]; then
        CONFIG_FILE="/boot/firmware/config.txt"
    elif [ -f "/boot/uEnv.txt" ]; then
        CONFIG_FILE="/boot/uEnv.txt"
    else
        echo "Could not find appropriate boot configuration file."
        return 1
    fi
    
    # Backup the config file
    cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    
    # Add or update display settings
    if [ -f "/boot/uEnv.txt" ]; then
        # For BeaglePlay with uEnv.txt
        if ! grep -q "video=" "$CONFIG_FILE"; then
            echo "Adding video parameter to uEnv.txt..."
            echo "optargs=video=HDMI-A-1:1920x1080@60" >> "$CONFIG_FILE"
        else
            echo "Updating existing video parameter..."
            sed -i 's/video=[^ ]*/video=HDMI-A-1:1920x1080@60/g' "$CONFIG_FILE"
        fi
    else
        # For config.txt style
        echo "Adding HDMI settings to config.txt..."
        echo "hdmi_group=2" >> "$CONFIG_FILE"
        echo "hdmi_mode=82" >> "$CONFIG_FILE"  # CEA mode 82 is 1920x1080 @ 60Hz
        echo "hdmi_drive=2" >> "$CONFIG_FILE"  # Normal HDMI mode
    fi
    
    echo "Boot configuration updated. A reboot is required for changes to take effect."
    echo "Would you like to reboot now? (y/n)"
    read -r reboot_response
    if [[ "$reboot_response" =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        reboot
    fi
    
    return 0
}

# Main execution
if check_beagleplay; then
    if detect_displays; then
        set_resolution
    else
        echo "Please connect an HDMI display and try again."
        exit 1
    fi
else
    echo "Exiting without making changes."
    exit 1
fi

echo "HDMI configuration complete."
echo "Your BeaglePlay should now be configured to use a 1920x1080 HDMI display."
