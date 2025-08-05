#!/bin/bash
# Comprehensive fix for all tCam-Mini component dependencies

set -e

echo "🔧 Fixing all tCam-Mini component dependencies"
echo "=============================================="

cd tcam-firmware

# 1. Fix clock component - needs main for system_config.h
echo "📝 Fixing clock component..."
cat > components/clock/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "time_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver lwip main)
EOF

# 2. Fix cmd component - needs lepton for cci.h and other dependencies
echo "📝 Fixing cmd component..."
cat > components/cmd/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "cmd_utilities.c"
                            "json_utilities.c"
                            "upd_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver espressif__mdns lepton sys clock i2c main)
EOF

# 3. Fix lepton component - needs main for system_config.h
echo "📝 Fixing lepton component..."
cat > components/lepton/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "cci.c"
                            "lepton_utilities.c"
                            "vospi.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver main i2c)
EOF

# 4. Fix i2c component - needs main for system_config.h
echo "📝 Fixing i2c component..."
cat > components/i2c/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "i2c.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver main)
EOF

# 5. Fix sys component - needs all dependencies
echo "📝 Fixing sys component..."
cat > components/sys/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "eth_utilities.c"
                            "net_utilities.c" 
                            "ps_utilities.c"
                            "sif_utilities.c"
                            "sys_utilities.c"
                            "wifi_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_netif nvs_flash json app_update espressif__mdns console main)
EOF

# 6. Fix the i2c driver include issue - ESP-IDF v5.5 uses different headers
echo "📝 Fixing i2c driver includes..."
sed -i 's/#include "driver\/i2c_master.h"/#include "driver\/i2c.h"/' components/i2c/i2c.c

# 7. Clean build directory
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ All component dependencies fixed!"
echo "===================================="
echo ""
echo "🚀 Ready to build! Run: ../test_build.sh"
