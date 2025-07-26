#ifndef CONFIG_H
#define CONFIG_H

// Version information
#define FIRMWARE_VERSION "1.0.0"
#define DEVICE_NAME "Feather-S3D-Sensors"

// WiFi Configuration
#define WIFI_SSID "your_wifi_ssid"        // Replace with your WiFi SSID
#define WIFI_PASSWORD "your_wifi_password" // Replace with your WiFi password
#define WIFI_TIMEOUT_MS 30000              // WiFi connection timeout
#define WIFI_RETRY_DELAY_MS 5000           // Delay between WiFi retry attempts

// Network Configuration
#define HTTP_PORT 80                       // HTTP server port
#define MDNS_NAME "feather-sensors"        // mDNS hostname
#define CORS_ENABLED true                  // Enable CORS headers

// I2C Configuration
#define I2C1_SDA_PIN 3                     // I2C1 SDA pin (LDO1)
#define I2C1_SCL_PIN 4                     // I2C1 SCL pin (LDO1)
#define I2C2_SDA_PIN 8                     // I2C2 SDA pin (LDO2)
#define I2C2_SCL_PIN 9                     // I2C2 SCL pin (LDO2)
#define I2C_FREQ 100000                    // I2C frequency (100kHz)

// Sensor Configuration
#define SHT45_I2C_ADDRESS 0x44             // SHT45 I2C address
#define HDC3022_I2C_ADDRESS 0x44           // HDC3022 I2C address (on separate bus)
#define SENSOR_READ_INTERVAL_MS 1000       // Sensor reading interval
#define SENSOR_TIMEOUT_MS 5000             // Sensor read timeout
#define SENSOR_RETRY_COUNT 3               // Number of retries for failed reads
#define SENSOR_ERROR_THRESHOLD 5           // Max consecutive errors before marking sensor as failed

// Status LED Configuration
#define STATUS_LED_PIN 13                  // Built-in LED pin
#define LED_BLINK_INTERVAL_MS 500          // LED blink interval for status indication

// System Configuration
#define SERIAL_BAUD_RATE 115200            // Serial communication baud rate
#define WATCHDOG_TIMEOUT_MS 30000          // Watchdog timer timeout
#define HEAP_WARNING_THRESHOLD 10000       // Free heap warning threshold (bytes)

// HTTP Response Configuration
#define HTTP_RESPONSE_TIMEOUT_MS 5000      // HTTP response timeout
#define MAX_CONCURRENT_CLIENTS 4           // Maximum concurrent HTTP clients
#define JSON_BUFFER_SIZE 1024              // JSON response buffer size

// Error Handling Configuration
#define MAX_ERROR_LOG_ENTRIES 10           // Maximum error log entries to keep
#define ERROR_RESET_THRESHOLD 100          // Reset device after this many critical errors

// Sensor Calibration (if needed)
#define SHT45_TEMP_OFFSET 0.0              // Temperature offset for SHT45 (°C)
#define SHT45_HUMIDITY_OFFSET 0.0          // Humidity offset for SHT45 (%)
#define HDC3022_TEMP_OFFSET 0.0            // Temperature offset for HDC3022 (°C)
#define HDC3022_HUMIDITY_OFFSET 0.0        // Humidity offset for HDC3022 (%)

// Debug Configuration
#define DEBUG_ENABLED true                 // Enable debug output
#define DEBUG_SENSOR_READINGS false        // Enable detailed sensor debug output
#define DEBUG_HTTP_REQUESTS false          // Enable HTTP request debugging
#define DEBUG_WIFI_CONNECTION false        // Enable WiFi connection debugging

// Status Codes
enum SensorStatus {
    SENSOR_OK = 0,
    SENSOR_ERROR_COMMUNICATION = 1,
    SENSOR_ERROR_TIMEOUT = 2,
    SENSOR_ERROR_INVALID_DATA = 3,
    SENSOR_ERROR_NOT_CONNECTED = 4,
    SENSOR_ERROR_CALIBRATION = 5
};

// System Status Codes
enum SystemStatus {
    SYSTEM_OK = 0,
    SYSTEM_WIFI_DISCONNECTED = 1,
    SYSTEM_LOW_MEMORY = 2,
    SYSTEM_SENSOR_FAILURE = 3,
    SYSTEM_CRITICAL_ERROR = 4
};

// LED Status Patterns
enum LEDStatus {
    LED_OFF = 0,
    LED_SOLID_BLUE,      // WiFi connected, sensors OK
    LED_BLINK_BLUE,      // WiFi connecting
    LED_SOLID_GREEN,     // Sensors reading successfully
    LED_BLINK_RED,       // Sensor error
    LED_SOLID_RED        // WiFi connection failed
};

// Sensor Data Structure
struct SensorReading {
    float temperature;
    float humidity;
    SensorStatus status;
    unsigned long last_read_time;
    int error_count;
    bool connected;
};

// System Information Structure
struct SystemInfo {
    String version;
    unsigned long uptime;
    size_t free_heap;
    bool wifi_connected;
    int wifi_rssi;
    String ip_address;
    SystemStatus status;
};

#endif // CONFIG_H