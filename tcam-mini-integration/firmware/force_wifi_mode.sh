#!/bin/bash
# Force tCam-Mini to use WiFi mode instead of Serial mode
# This fixes the issue where GPIO32 detection causes the device to run in serial mode

set -e

FIRMWARE_DIR="/home/lio/github/greenhouse-monitoring/tcam-mini-integration/firmware/tcam-firmware"

echo "🔧 Forcing tCam-Mini to WiFi Mode"
echo "=================================="
echo
echo "Issue: GPIO32 is being detected as LOW, causing Serial mode"
echo "Solution: Force WiFi mode in firmware"
echo

# Backup the original file
cp "$FIRMWARE_DIR/main/ctrl_task.c" "$FIRMWARE_DIR/main/ctrl_task.c.backup"
echo "✅ Backed up original ctrl_task.c"

# Create the fix
cat > /tmp/ctrl_task_fix.patch << 'EOF'
--- a/main/ctrl_task.c
+++ b/main/ctrl_task.c
@@ -191,10 +191,13 @@ static void ctrl_task_init()
 		gpio_reset_pin(BRD_W_MODE_SENSE_IO);
 		gpio_set_direction(BRD_W_MODE_SENSE_IO, GPIO_MODE_INPUT);
 		gpio_set_pull_mode(BRD_W_MODE_SENSE_IO, GPIO_PULLUP_ONLY);
-		if (gpio_get_level(BRD_W_MODE_SENSE_IO) == 0) {
-			ctrl_if_mode = CTRL_IF_MODE_SIF;
-			ESP_LOGI(TAG, "WiFi board type detected - using Serial");
-		} else {
+		// FORCE WiFi mode - ignore GPIO32 detection
+		// Original code: if (gpio_get_level(BRD_W_MODE_SENSE_IO) == 0)
+		// GPIO32 is incorrectly reading LOW, causing Serial mode
+		// For greenhouse monitoring, we need WiFi mode with socket server
+		if (false) {  // Never enter serial mode
+			ctrl_if_mode = CTRL_IF_MODE_SIF;
+			ESP_LOGI(TAG, "WiFi board type detected - using Serial (DISABLED)");
+		} else {
 			ctrl_if_mode = CTRL_IF_MODE_WIFI;
 			ESP_LOGI(TAG, "WiFi board type detected - using WiFi");
 		}
EOF

# Apply the fix directly to the source file
echo "🔨 Applying WiFi mode fix..."

# Use sed to make the change
sed -i 's/if (gpio_get_level(BRD_W_MODE_SENSE_IO) == 0) {/if (false) {  \/\/ FORCE WiFi MODE - GPIO32 fix/' "$FIRMWARE_DIR/main/ctrl_task.c"
sed -i 's/ESP_LOGI(TAG, "WiFi board type detected - using Serial");/ESP_LOGI(TAG, "WiFi board type detected - using Serial (DISABLED)");/' "$FIRMWARE_DIR/main/ctrl_task.c"

echo "✅ Applied WiFi mode fix"

# Verify the change
echo
echo "🔍 Verifying changes..."
if grep -q "if (false)" "$FIRMWARE_DIR/main/ctrl_task.c"; then
    echo "✅ Fix applied successfully"
    echo
    echo "📋 Changes made:"
    echo "   - GPIO32 detection bypassed"
    echo "   - WiFi mode forced ON"
    echo "   - Serial mode disabled"
    echo
    echo "🎯 Next steps:"
    echo "   1. Rebuild firmware: cd firmware/tcam-firmware && idf.py build"
    echo "   2. Flash firmware: idf.py -p /dev/ttyUSB0 flash"
    echo "   3. Test socket communication on port 5001"
else
    echo "❌ Fix may not have applied correctly"
    echo "Please check the file manually"
fi

echo
echo "💡 To restore original behavior:"
echo "   cp $FIRMWARE_DIR/main/ctrl_task.c.backup $FIRMWARE_DIR/main/ctrl_task.c"
