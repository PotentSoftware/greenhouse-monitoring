/*
 * Station Mode Configuration Utility
 * 
 * This utility configures the tCam-Mini to connect to a home WiFi network
 * instead of creating its own access point.
 * 
 * Add this to main.c to configure station mode on first boot.
 */

#include "ps_utilities.h"
#include "net_utilities.h"
#include "esp_log.h"
#include <string.h>

static const char* TAG = "station_config";

void configure_station_mode(void) {
    net_info_t net_info;
    
    ESP_LOGI(TAG, "Configuring tCam-Mini for station mode...");
    
    // Get current network configuration
    ps_get_net_info(&net_info);
    
    // Configure for station mode
    strcpy(net_info.sta_ssid, "BT-X6F962");           // Your home WiFi SSID
    strcpy(net_info.sta_pw, "");                      // WiFi password (empty for now - you'll need to set this)
    
    // Set client mode flag
    net_info.flags |= NET_INFO_FLAG_CLIENT_MODE;
    net_info.flags |= NET_INFO_FLAG_STARTUP_ENABLE;
    
    // Configure IP settings (use DHCP by default)
    net_info.sta_ip_addr[0] = 0;   // 0.0.0.0 means use DHCP
    net_info.sta_ip_addr[1] = 0;
    net_info.sta_ip_addr[2] = 0;
    net_info.sta_ip_addr[3] = 0;
    
    net_info.sta_netmask[0] = 255;
    net_info.sta_netmask[1] = 255;
    net_info.sta_netmask[2] = 255;
    net_info.sta_netmask[3] = 0;
    
    // Save the configuration
    ps_set_net_info(&net_info);
    
    ESP_LOGI(TAG, "Station mode configured:");
    ESP_LOGI(TAG, "  SSID: %s", net_info.sta_ssid);
    ESP_LOGI(TAG, "  Flags: 0x%02X", net_info.flags);
    ESP_LOGI(TAG, "  Client mode: %s", (net_info.flags & NET_INFO_FLAG_CLIENT_MODE) ? "YES" : "NO");
    
    ESP_LOGI(TAG, "Reboot required for changes to take effect");
}

/* 
 * Alternative: Configure via NVS directly (more reliable)
 * This bypasses the normal configuration and directly sets NVS values
 */
void force_station_mode_nvs(void) {
    ESP_LOGI(TAG, "Force configuring station mode via NVS...");
    
    // This would require direct NVS manipulation
    // For now, use the ps_utilities approach above
}
