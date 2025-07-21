#!/bin/bash
# Script to configure HDMI display on BeaglePlay at 1920x1080 resolution
# This script should be run on the BeaglePlay device

echo "Setting up HDMI display at 1920x1080 resolution..."

# Check if HDMI is connected
if ! xrandr | grep -q "HDMI"; then
    echo "Error: No HDMI display detected. Please ensure an HDMI display is connected."
    exit 1
fi

# Get the HDMI output name (might be HDMI-1, HDMI-0, etc.)
HDMI_OUTPUT=$(xrandr | grep "HDMI" | cut -d " " -f1)

# Check if the HDMI output was found
if [ -z "$HDMI_OUTPUT" ]; then
    echo "Error: Could not determine HDMI output name."
    exit 1
fi

echo "Detected HDMI output: $HDMI_OUTPUT"

# Set the resolution to 1920x1080
echo "Setting resolution to 1920x1080..."
xrandr --output $HDMI_OUTPUT --mode 1920x1080

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Successfully set HDMI display to 1920x1080 resolution."
else
    echo "Failed to set resolution. Trying to add the mode..."
    
    # Try to add the mode if it doesn't exist
    xrandr --newmode "1920x1080_60.00" 173.00 1920 2048 2248 2576 1080 1083 1088 1120 -hsync +vsync
    xrandr --addmode $HDMI_OUTPUT "1920x1080_60.00"
    xrandr --output $HDMI_OUTPUT --mode "1920x1080_60.00"
    
    if [ $? -eq 0 ]; then
        echo "Successfully added and set custom 1920x1080 mode."
    else
        echo "Error: Failed to set HDMI resolution. Please check your display compatibility."
        exit 1
    fi
fi

# Make the display persistent across reboots by adding to .xprofile
echo "Making settings persistent..."
echo "#!/bin/bash" > ~/.xprofile
echo "xrandr --output $HDMI_OUTPUT --mode 1920x1080" >> ~/.xprofile
chmod +x ~/.xprofile

echo "HDMI display configuration complete."
echo "Your BeaglePlay is now configured to use a 1920x1080 HDMI display."
