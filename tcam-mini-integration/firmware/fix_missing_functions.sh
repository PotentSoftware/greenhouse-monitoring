#!/bin/bash
# Fix missing function implementations for tCam-Mini firmware

set -e

echo "🔧 Adding missing function implementations"
echo "=========================================="

cd tcam-firmware

# 1. Add missing I2C functions to i2c component
echo "📝 Adding missing I2C functions..."
cat >> components/i2c/i2c_utilities.c << 'EOF'

// Missing I2C functions for ESP-IDF v5.5 compatibility
static SemaphoreHandle_t i2c_mutex = NULL;

void i2c_lock(void) {
    if (i2c_mutex == NULL) {
        i2c_mutex = xSemaphoreCreateMutex();
    }
    if (i2c_mutex != NULL) {
        xSemaphoreTake(i2c_mutex, portMAX_DELAY);
    }
}

void i2c_unlock(void) {
    if (i2c_mutex != NULL) {
        xSemaphoreGive(i2c_mutex);
    }
}

esp_err_t i2c_master_write_slave(i2c_port_t i2c_num, uint8_t* data_wr, size_t size, TickType_t ticks_to_wait) {
    return i2c_master_write_to_device(i2c_num, I2C_ADDR_8BIT_WRITE(0x2A), data_wr, size, ticks_to_wait);
}

esp_err_t i2c_master_read_slave(i2c_port_t i2c_num, uint8_t* data_rd, size_t size, TickType_t ticks_to_wait) {
    return i2c_master_read_from_device(i2c_num, I2C_ADDR_8BIT_READ(0x2A), data_rd, size, ticks_to_wait);
}
EOF

# 2. Add missing time functions to clock component
echo "📝 Adding missing time functions..."
cat >> components/clock/clock_utilities.c << 'EOF'

// Missing time functions for ESP-IDF v5.5 compatibility
static struct timeval current_time = {0, 0};

void time_init(void) {
    // Initialize time - can be enhanced later with RTC/NTP
    gettimeofday(&current_time, NULL);
}

void time_set(struct timeval* tv) {
    if (tv != NULL) {
        current_time = *tv;
        settimeofday(tv, NULL);
    }
}

void time_get(struct timeval* tv) {
    if (tv != NULL) {
        gettimeofday(tv, NULL);
    }
}
EOF

# 3. Update I2C component header to declare new functions
echo "📝 Updating I2C header..."
cat >> components/i2c/i2c_utilities.h << 'EOF'

// Additional I2C function declarations
void i2c_lock(void);
void i2c_unlock(void);
esp_err_t i2c_master_write_slave(i2c_port_t i2c_num, uint8_t* data_wr, size_t size, TickType_t ticks_to_wait);
esp_err_t i2c_master_read_slave(i2c_port_t i2c_num, uint8_t* data_rd, size_t size, TickType_t ticks_to_wait);
EOF

# 4. Update clock component header to declare new functions
echo "📝 Updating clock header..."
cat >> components/clock/clock_utilities.h << 'EOF'

// Additional time function declarations
void time_init(void);
void time_set(struct timeval* tv);
void time_get(struct timeval* tv);
EOF

# 5. Add necessary includes to I2C component
echo "📝 Adding includes to I2C component..."
sed -i '1i #include "freertos/FreeRTOS.h"' components/i2c/i2c_utilities.c
sed -i '2i #include "freertos/semphr.h"' components/i2c/i2c_utilities.c
sed -i '3i #include "driver/i2c.h"' components/i2c/i2c_utilities.c

# 6. Add necessary includes to clock component
echo "📝 Adding includes to clock component..."
sed -i '1i #include <sys/time.h>' components/clock/clock_utilities.c

# 7. Clean build directory
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ Missing function implementations added!"
echo "========================================"
echo ""
echo "🚀 Now try building again with: idf.py build"
