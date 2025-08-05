#ifndef I2C_UTILITIES_H
#define I2C_UTILITIES_H

#include "driver/i2c.h"
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

// I2C initialization and management functions
esp_err_t i2c_master_init(int scl_pin, int sda_pin);
void i2c_lock(void);
void i2c_unlock(void);
esp_err_t i2c_master_write_slave(uint8_t slave_addr, uint8_t* data_wr, size_t size);
esp_err_t i2c_master_read_slave(uint8_t slave_addr, uint8_t* data_rd, size_t size);

#ifdef __cplusplus
}
#endif

#endif // I2C_UTILITIES_H
