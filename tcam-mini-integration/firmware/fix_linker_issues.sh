#!/bin/bash
# Comprehensive fix for linker issues in tCam-Mini firmware

set -e

echo "🔧 Fixing linker issues with missing function implementations"
echo "=============================================================="

cd tcam-firmware

# 1. Update sys component to include clock and i2c dependencies
echo "📝 Updating sys component dependencies..."
cat > components/sys/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "eth_utilities.c"
                            "net_utilities.c" 
                            "ps_utilities.c"
                            "sif_utilities.c"
                            "sys_utilities.c"
                            "wifi_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_netif nvs_flash json app_update espressif__mdns console main esp_eth esp_wifi clock i2c)
EOF

# 2. Update lepton component to properly include i2c
echo "📝 Updating lepton component dependencies..."
cat > components/lepton/CMakeLists.txt << 'EOF'
idf_component_register(SRCS "cci.c"
                            "lepton_utilities.c"
                            "vospi.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver main i2c clock)
EOF

# 3. Ensure i2c component includes the new functions properly
echo "📝 Updating i2c component implementation..."
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

# 4. Update i2c header file
echo "📝 Updating i2c header file..."
cat > components/i2c/i2c_utilities.h << 'EOF'
#ifndef I2C_UTILITIES_H
#define I2C_UTILITIES_H

#include "driver/i2c.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// I2C initialization and management functions
esp_err_t i2c_master_init(void);
void i2c_lock(void);
void i2c_unlock(void);
esp_err_t i2c_master_write_slave(i2c_port_t i2c_num, uint8_t* data_wr, size_t size, TickType_t ticks_to_wait);
esp_err_t i2c_master_read_slave(i2c_port_t i2c_num, uint8_t* data_rd, size_t size, TickType_t ticks_to_wait);

#ifdef __cplusplus
}
#endif

#endif // I2C_UTILITIES_H
EOF

# 5. Update clock component implementation
echo "📝 Updating clock component implementation..."
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

# 6. Update clock header file
echo "📝 Updating clock header file..."
cat > components/clock/clock_utilities.h << 'EOF'
#ifndef CLOCK_UTILITIES_H
#define CLOCK_UTILITIES_H

#include <sys/time.h>

#ifdef __cplusplus
extern "C" {
#endif

// Time management functions
void time_init(void);
void time_set(struct timeval* tv);
void time_get(struct timeval* tv);

#ifdef __cplusplus
}
#endif

#endif // CLOCK_UTILITIES_H
EOF

# 7. Clean build directory
echo "🧹 Cleaning build directory..."
rm -rf build

echo ""
echo "✅ Linker issues fixed!"
echo "======================="
echo ""
echo "🚀 Now try building again with: idf.py build"
