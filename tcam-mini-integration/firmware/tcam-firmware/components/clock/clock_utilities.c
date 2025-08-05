#include <sys/time.h>
#include <time.h>
#include <stdbool.h>
#include <inttypes.h>
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
        ESP_LOGI(TAG, "Time set to %" PRIu32 ".%06" PRIu32, (uint32_t)tv->tv_sec, (uint32_t)tv->tv_usec);
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
