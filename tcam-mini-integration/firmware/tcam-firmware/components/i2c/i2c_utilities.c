#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "driver/i2c.h"
#include "esp_log.h"
#include "i2c_utilities.h"

static const char* TAG = "i2c_utilities";

// I2C configuration
#define I2C_MASTER_NUM              I2C_NUM_0   /*!< I2C port number for master dev */
#define I2C_MASTER_FREQ_HZ          100000      /*!< I2C master clock frequency */
#define I2C_MASTER_TX_BUF_DISABLE   0           /*!< I2C master doesn't need buffer */
#define I2C_MASTER_RX_BUF_DISABLE   0           /*!< I2C master doesn't need buffer */

// Lepton I2C address
#define LEPTON_I2C_ADDR             0x2A

// Global mutex for I2C operations
static SemaphoreHandle_t i2c_mutex = NULL;
static bool i2c_initialized = false;

esp_err_t i2c_master_init(int scl_pin, int sda_pin) {
    if (i2c_initialized) {
        return ESP_OK;
    }
    
    ESP_LOGI(TAG, "Initializing I2C master with SCL=%d, SDA=%d", scl_pin, sda_pin);
    
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = sda_pin,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_io_num = scl_pin,
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

esp_err_t i2c_master_write_slave(uint8_t slave_addr, uint8_t* data_wr, size_t size) {
    ESP_LOGD(TAG, "I2C write to slave 0x%02X, size %d", slave_addr, size);
    esp_err_t ret = i2c_master_write_to_device(I2C_MASTER_NUM, slave_addr, data_wr, size, 1000 / portTICK_PERIOD_MS);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C write failed: %s (0x%02X)", esp_err_to_name(ret), ret);
    }
    return ret;
}

esp_err_t i2c_master_read_slave(uint8_t slave_addr, uint8_t* data_rd, size_t size) {
    ESP_LOGD(TAG, "I2C read from slave 0x%02X, size %d", slave_addr, size);
    esp_err_t ret = i2c_master_read_from_device(I2C_MASTER_NUM, slave_addr, data_rd, size, 1000 / portTICK_PERIOD_MS);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "I2C read failed: %s (0x%02X)", esp_err_to_name(ret), ret);
    }
    return ret;
}
