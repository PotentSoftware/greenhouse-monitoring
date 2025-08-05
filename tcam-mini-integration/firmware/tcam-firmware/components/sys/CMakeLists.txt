idf_component_register(SRCS "eth_utilities.c"
                            "net_utilities.c" 
                            "ps_utilities.c"
                            "sif_utilities.c"
                            "sys_utilities.c"
                            "wifi_utilities.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver esp_netif nvs_flash json app_update espressif__mdns console main esp_eth esp_wifi clock i2c)
