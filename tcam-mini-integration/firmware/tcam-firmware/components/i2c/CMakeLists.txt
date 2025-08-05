idf_component_register(SRCS "i2c_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_driver_i2c freertos)
