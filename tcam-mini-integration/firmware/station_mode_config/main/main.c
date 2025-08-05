/*
 * tCam-Mini Station Mode Configurator
 * 
 * This utility configures the tCam-Mini to connect to a home WiFi network
 * instead of creating its own access point.
 * 
 * Flash this utility, let it run once, then flash back the normal firmware.
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "nvs.h"

static const char* TAG = "station_config";

// Network info structure (must match tCam firmware ps_net_info_t)
#define PS_SSID_MAX_LEN 32
#define PS_PW_MAX_LEN 63

typedef struct {
    char ap_ssid[PS_SSID_MAX_LEN+1];   // AP SSID
    char sta_ssid[PS_SSID_MAX_LEN+1];  // Station SSID  
    char ap_pw[PS_PW_MAX_LEN+1];       // AP password
    char sta_pw[PS_PW_MAX_LEN+1];      // Station password
    uint8_t flags;                     // Network flags
    uint8_t ap_ip_addr[4];            // AP IP address
    uint8_t sta_ip_addr[4];           // Station IP address
    uint8_t sta_netmask[4];           // Station netmask
} ps_net_info_t;

// Network flags (from tCam firmware)
#define NET_INFO_FLAG_STARTUP_ENABLE 0x01
#define NET_INFO_FLAG_CLIENT_MODE    0x80

#define WIFI_SSID "BT-X6F962"
#define WIFI_PASSWORD "N7nCfV3RE6d4Ra"

void configure_station_mode(void) {
    nvs_handle_t nvs_handle;
    esp_err_t err;
    ps_net_info_t net_info;
    
    ESP_LOGI(TAG, "=== tCam-Mini Station Mode Configurator ===");
    
    // Initialize NVS
    err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    
    // Open NVS storage namespace
    err = nvs_open("storage", NVS_READWRITE, &nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error opening NVS handle: %s", esp_err_to_name(err));
        return;
    }
    
    // Try to read existing WiFi configuration
    size_t required_size = sizeof(ps_net_info_t);
    err = nvs_get_blob(nvs_handle, "wifi_info", &net_info, &required_size);
    
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGI(TAG, "No existing WiFi config found, creating new one");
        memset(&net_info, 0, sizeof(ps_net_info_t));
        
        // Set default AP SSID (camera name)
        strcpy(net_info.ap_ssid, "tCam-Mini-CDE9");
        strcpy(net_info.ap_pw, "");
        
        // Set default AP IP
        net_info.ap_ip_addr[0] = 192;
        net_info.ap_ip_addr[1] = 168;
        net_info.ap_ip_addr[2] = 4;
        net_info.ap_ip_addr[3] = 1;
        
    } else if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error reading WiFi config: %s", esp_err_to_name(err));
        nvs_close(nvs_handle);
        return;
    } else {
        ESP_LOGI(TAG, "Found existing WiFi config");
    }
    
    // Configure for station mode
    ESP_LOGI(TAG, "Configuring for station mode...");
    
    // Set your home WiFi credentials
    strcpy(net_info.sta_ssid, WIFI_SSID);
    strcpy(net_info.sta_pw, WIFI_PASSWORD);
    
    // Enable client mode and startup
    net_info.flags |= NET_INFO_FLAG_CLIENT_MODE;
    net_info.flags |= NET_INFO_FLAG_STARTUP_ENABLE;
    
    // Use DHCP (set IP to 0.0.0.0)
    net_info.sta_ip_addr[0] = 0;
    net_info.sta_ip_addr[1] = 0;
    net_info.sta_ip_addr[2] = 0;
    net_info.sta_ip_addr[3] = 0;
    
    // Set netmask
    net_info.sta_netmask[0] = 255;
    net_info.sta_netmask[1] = 255;
    net_info.sta_netmask[2] = 255;
    net_info.sta_netmask[3] = 0;
    
    // Write the configuration to NVS
    err = nvs_set_blob(nvs_handle, "wifi_info", &net_info, sizeof(ps_net_info_t));
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error writing WiFi config: %s", esp_err_to_name(err));
        nvs_close(nvs_handle);
        return;
    }
    
    // Commit the changes
    err = nvs_commit(nvs_handle);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Error committing NVS: %s", esp_err_to_name(err));
        nvs_close(nvs_handle);
        return;
    }
    
    nvs_close(nvs_handle);
    
    ESP_LOGI(TAG, "✅ Station mode configuration complete!");
    ESP_LOGI(TAG, "Configuration:");
    ESP_LOGI(TAG, "  WiFi SSID: %s", net_info.sta_ssid);
    ESP_LOGI(TAG, "  Flags: 0x%02X", net_info.flags);
    ESP_LOGI(TAG, "  Client mode: %s", (net_info.flags & NET_INFO_FLAG_CLIENT_MODE) ? "ENABLED" : "DISABLED");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "⚠️  IMPORTANT: Set your WiFi password in the source code!");
    ESP_LOGI(TAG, "⚠️  Then reflash the normal tCam firmware for changes to take effect.");
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Device will restart in 10 seconds...");
}

void app_main(void) {
    configure_station_mode();
    
    // Wait 10 seconds then restart
    for (int i = 10; i >= 1; i--) {
        ESP_LOGI(TAG, "Restarting in %d seconds...", i);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
    
    ESP_LOGI(TAG, "Restarting now!");
    esp_restart();
}
