set(SOURCES main.c ctrl_task.c lep_task.c mon_task.c net_cmd_task.c rsp_task.c sif_cmd_task.c)
idf_component_register(SRCS ${SOURCES}
                    INCLUDE_DIRS .
                    REQUIRES clock cmd i2c lepton sys app_update esp_driver_gpio)
