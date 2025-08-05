#!/bin/bash
# Final compatibility fixes for tCam-Mini firmware

set -e

echo "🔧 Applying final compatibility fixes"
echo "====================================="

cd tcam-firmware

# 1. Fix cmd component - add app_update dependency
echo "📝 Fixing cmd component app_update dependency..."
cat > components/cmd/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "cmd_utilities.c"
                            "json_utilities.c"
                            "upd_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver espressif__mdns lepton sys clock i2c main app_update)
EOF

# 2. Fix format string issues in wifi_utilities.c
echo "📝 Fixing format string issues in wifi_utilities.c..."
sed -i 's/"Station:"MACSTR" join, AID=%d"/"Station:" MACSTR " join, AID=%d"/' components/sys/wifi_utilities.c
sed -i 's/"Station:"MACSTR" leave, AID=%d"/"Station:" MACSTR " leave, AID=%d"/' components/sys/wifi_utilities.c

# 3. Add missing includes for format specifiers
echo "📝 Adding missing inttypes.h includes..."
sed -i '1i#include <inttypes.h>' components/sys/wifi_utilities.c

# 4. Clean build directory
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ Final fixes applied!"
echo "======================"
echo ""
echo "🚀 Ready for final build test!"
