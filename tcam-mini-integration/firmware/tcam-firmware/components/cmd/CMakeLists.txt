idf_component_register(SRCS "cmd_utilities.c"
                            "json_utilities.c"
                            "upd_utilities.c"
                    INCLUDE_DIRS "."
                    REQUIRES json
                    PRIV_REQUIRES driver espressif__mdns lepton sys clock i2c main app_update mbedtls)
