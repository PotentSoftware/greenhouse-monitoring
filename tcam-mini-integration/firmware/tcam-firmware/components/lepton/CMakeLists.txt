idf_component_register(SRCS "cci.c"
                            "lepton_utilities.c"
                            "vospi.c"
                    INCLUDE_DIRS "."
                    PRIV_REQUIRES driver main i2c clock)
