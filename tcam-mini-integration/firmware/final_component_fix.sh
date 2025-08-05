#!/bin/bash
# Final fix for component configuration and missing functions

set -e

echo "🔧 Final component configuration fix"
echo "===================================="

cd tcam-firmware

# 1. Fix i2c component CMakeLists.txt to use correct source file
echo "📝 Fixing i2c component CMakeLists.txt..."
cat > components/i2c/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "i2c_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_driver_i2c freertos)
EOF

# 2. Fix clock component CMakeLists.txt to use correct source file
echo "📝 Fixing clock component CMakeLists.txt..."
cat > components/clock/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "clock_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver)
EOF

# 3. Ensure the i2c_utilities.c file exists and is properly configured
echo "📝 Ensuring i2c_utilities.c exists..."
if [ ! -f "components/i2c/i2c_utilities.c" ]; then
    echo "Creating i2c_utilities.c..."
    cat > components/i2c/i2c_utilities.c << 'EOF'
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include "i2c_utilities.h"

static const char* TAG = "i2c_utilities";

// I2C configuration
#define I2C_MASTER_SCL_IO           22    /*!< gpio number for I2C master clock */
#define I2C_MASTER_SDA_IO           21    /*!< gpio number for I2C master data  */
#define I2C_MASTER_NUM              I2C_NUM_0   /*!< I2C port number for master dev */
#define I2C_MASTER_FREQ_HZ          100000      /*!< I2C master clock frequency */
#define I2C_MASTER_TX_BUF_DISABLE   0           /*!< I2C master doesn't need buffer */
#define I2C_MASTER_RX_BUF_DISABLE   0           /*!< I2C master doesn't need buffer */

// Lepton I2C address
#define LEPTON_I2C_ADDR             0x2A

// Global mutex for I2C operations
static SemaphoreHandle_t i2c_mutex = NULL;
static bool i2c_initialized = false;

esp_err_t i2c_master_init(void) {
    if (i2c_initialized) {
        return ESP_OK;
    }
    
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_MASTER_SDA_IO,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = I2C_MASTER_SCL_IO,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_MASTER_FREQ_HZ,
    };
    
    esp_err_t err = i2c_param_config(I2C_MASTER_NUM, &conf);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "I2C param config failed: %s", esp_err_to_name(err));
        return err;
    }
    
    err = i2c_driver_install(I2C_MASTER_NUM, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "I2C driver install failed: %s", esp_err_to_name(err));
        return err;
    }
    
    // Create mutex for thread safety
    if (i2c_mutex == NULL) {
        i2c_mutex = xSemaphoreCreateMutex();
        if (i2c_mutex == NULL) {
            ESP_LOGE(TAG, "Failed to create I2C mutex");
            return ESP_ERR_NO_MEM;
        }
    }
    
    i2c_initialized = true;
    ESP_LOGI(TAG, "I2C master initialized successfully");
    return ESP_OK;
}

void i2c_lock(void) {
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
    return i2c_master_write_to_device(i2c_num, LEPTON_I2C_ADDR, data_wr, size, ticks_to_wait);
}

esp_err_t i2c_master_read_slave(i2c_port_t i2c_num, uint8_t* data_rd, size_t size, TickType_t ticks_to_wait) {
    return i2c_master_read_from_device(i2c_num, LEPTON_I2C_ADDR, data_rd, size, ticks_to_wait);
}
EOF
fi

# 4. Ensure the clock_utilities.c file exists and is properly configured
echo "📝 Ensuring clock_utilities.c exists..."
if [ ! -f "components/clock/clock_utilities.c" ]; then
    echo "Creating clock_utilities.c..."
    cat > components/clock/clock_utilities.c << 'EOF'
#include <sys/time.h>
#include <time.h>
#include "esp_log.h"
#include "clock_utilities.h"

static const char* TAG = "clock_utilities";

// Global time state
static struct timeval system_time = {0, 0};
static bool time_initialized = false;

void time_init(void) {
    if (!time_initialized) {
        // Initialize with current system time
        gettimeofday(&system_time, NULL);
        time_initialized = true;
        ESP_LOGI(TAG, "Time system initialized");
    }
}

void time_set(struct timeval* tv) {
    if (tv != NULL) {
        system_time = *tv;
        settimeofday(tv, NULL);
        ESP_LOGI(TAG, "Time set to %ld.%06ld", tv->tv_sec, tv->tv_usec);
    }
}

void time_get(struct timeval* tv) {
    if (tv != NULL) {
        if (time_initialized) {
            gettimeofday(tv, NULL);
        } else {
            *tv = system_time;
        }
    }
}
EOF
fi

# 5. Remove any old conflicting source files
echo "📝 Cleaning up old files..."
rm -f components/i2c/i2c.c
rm -f components/clock/time_utilities.c

# 6. Clean build directory
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ Final component configuration complete!"
echo "========================================"
echo ""
echo "🚀 Now try building again with: idf.py build"
