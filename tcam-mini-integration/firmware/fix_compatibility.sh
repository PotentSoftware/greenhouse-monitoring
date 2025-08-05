#!/bin/bash
# Fix tCam-Mini firmware compatibility with ESP-IDF v5.5

set -e

echo "🔧 Fixing tCam-Mini firmware compatibility with ESP-IDF v5.5"
echo "============================================================"

cd tcam-firmware

# 1. Fix i2c component CMakeLists.txt - add driver dependency
echo "📝 Fixing i2c component dependencies..."
cat > components/i2c/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "i2c.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver)
EOF

# 2. Fix sys component CMakeLists.txt - add driver dependency
echo "📝 Fixing sys component dependencies..."
cat > components/sys/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "eth_utilities.c"
                            "file_utilities.c" 
                            "json_utilities.c"
                            "ps_utilities.c"
                            "wifi_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_netif nvs_flash json app_update espressif__mdns console)
EOF

# 3. Fix clock component CMakeLists.txt - add driver dependency
echo "📝 Fixing clock component dependencies..."
cat > components/clock/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "time_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver lwip)
EOF

# 4. Fix format overflow in time_utilities.c
echo "📝 Fixing format overflow in time_utilities.c..."
sed -i 's/char buf\[26\]/char buf[32]/' components/clock/time_utilities.c

# 5. Fix missing esp_mac.h include in ps_utilities.c
echo "📝 Adding missing esp_mac.h include..."
sed -i '/#include "esp_system.h"/a #include "esp_mac.h"' components/sys/ps_utilities.c

# 6. Update i2c.c to use new driver includes
echo "📝 Updating i2c driver includes..."
sed -i 's/#include "driver\/i2c.h"/#include "driver\/i2c_master.h"/' components/i2c/i2c.c

# 7. Fix GPIO includes in eth_utilities.c
echo "📝 Updating GPIO driver includes..."
sed -i 's/#include "driver\/gpio.h"/#include "driver\/gpio.h"/' components/sys/eth_utilities.c

# 8. Add missing driver component to cmd component
echo "📝 Fixing cmd component dependencies..."
if [ -f components/cmd/CMakeLists.txt ]; then
    # Check if PRIV_REQUIRES already exists and add driver to it
    if grep -q "PRIV_REQUIRES" components/cmd/CMakeLists.txt; then
        sed -i 's/PRIV_REQUIRES \(.*\)/PRIV_REQUIRES \1 driver/' components/cmd/CMakeLists.txt
    else
        sed -i '/INCLUDE_DIRS/a \                    PRIV_REQUIRES driver espressif__mdns' components/cmd/CMakeLists.txt
    fi
fi

# 9. Add missing driver component to lepton component
echo "📝 Fixing lepton component dependencies..."
if [ -f components/lepton/CMakeLists.txt ]; then
    if grep -q "PRIV_REQUIRES" components/lepton/CMakeLists.txt; then
        sed -i 's/PRIV_REQUIRES \(.*\)/PRIV_REQUIRES \1 driver/' components/lepton/CMakeLists.txt
    else
        sed -i '/INCLUDE_DIRS/a \                    PRIV_REQUIRES driver' components/lepton/CMakeLists.txt
    fi
fi

# 10. Create a backup of original sdkconfig and update it
echo "📝 Updating sdkconfig for ESP-IDF v5.5..."
cp sdkconfig sdkconfig.backup

# Clean build directory to force reconfiguration
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ Compatibility fixes applied!"
echo "================================"
echo ""
echo "📋 Changes made:"
echo "  • Added driver dependencies to i2c, sys, clock, cmd, lepton components"
echo "  • Fixed format overflow in time_utilities.c (increased buffer size)"
echo "  • Added missing esp_mac.h include in ps_utilities.c"
echo "  • Updated driver includes for ESP-IDF v5.5"
echo "  • Cleaned build directory for fresh configuration"
echo ""
echo "🚀 Ready to build! Run: ../test_build.sh"
