#include <Arduino.h>
#include <WiFi.h>
#include "config.h"
#include "sensor_manager.h"
#include "web_server.h"

// Global variables
unsigned long last_sensor_read = 0;
unsigned long last_status_print = 0;
unsigned long boot_time = 0;
LEDStatus current_led_status = LED_OFF;
bool wifi_connected = false;

// Function prototypes
void setupWiFi();
void updateStatusLED();
void printSystemStatus();
void handleWiFiReconnection();
bool connectToWiFi();

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    delay(1000); // Allow serial to initialize
    
    boot_time = millis();
    
    Serial.println("\n" + String("=").repeat(50));
    Serial.println("🌱 Feather S3[D] Precision Sensors");
    Serial.println("Version: " + String(FIRMWARE_VERSION));
    Serial.println("Device: " + String(DEVICE_NAME));
    Serial.println(String("=").repeat(50));
    
    // Configure status LED
    pinMode(STATUS_LED_PIN, OUTPUT);
    digitalWrite(STATUS_LED_PIN, LOW);
    current_led_status = LED_OFF;
    
    // Initialize WiFi
    Serial.println("Initializing WiFi...");
    setupWiFi();
    
    // Initialize sensor manager
    Serial.println("Initializing sensors...");
    if (!sensorManager.begin()) {
        Serial.println("ERROR: Failed to initialize sensors!");
        current_led_status = LED_SOLID_RED;
    } else {
        Serial.println("Sensors initialized successfully");
        current_led_status = LED_SOLID_GREEN;
    }
    
    // Perform initial sensor self-test
    if (sensorManager.areAnySensorsConnected()) {
        Serial.println("Performing sensor self-test...");
        if (sensorManager.performSelfTest()) {
            Serial.println("Self-test completed successfully");
        } else {
            Serial.println("WARNING: Self-test failed for some sensors");
        }
    }
    
    // Initialize web server
    if (wifi_connected) {
        Serial.println("Starting web server...");
        if (webServer.begin()) {
            Serial.println("Web server started successfully");
            current_led_status = LED_SOLID_BLUE;
        } else {
            Serial.println("ERROR: Failed to start web server");
            current_led_status = LED_BLINK_RED;
        }
    }
    
    // Print initial system status
    printSystemStatus();
    
    Serial.println("Setup completed!");
    Serial.println("System ready for operation.\n");
}

void loop() {
    unsigned long current_time = millis();
    
    // Handle WiFi reconnection if needed
    handleWiFiReconnection();
    
    // Handle web server requests
    if (wifi_connected && webServer.isRunning()) {
        webServer.handle();
    }
    
    // Read sensors at specified interval
    if (current_time - last_sensor_read >= SENSOR_READ_INTERVAL_MS) {
        if (DEBUG_SENSOR_READINGS) {
            Serial.println("Reading sensors...");
        }
        
        bool read_success = sensorManager.readAllSensors();
        
        if (read_success) {
            if (wifi_connected) {
                current_led_status = LED_SOLID_BLUE;
            } else {
                current_led_status = LED_SOLID_GREEN;
            }
        } else {
            Serial.println("WARNING: Sensor read failed");
            current_led_status = LED_BLINK_RED;
        }
        
        last_sensor_read = current_time;
    }
    
    // Update status LED
    updateStatusLED();
    
    // Print system status periodically (every 30 seconds)
    if (current_time - last_status_print >= 30000) {
        printSystemStatus();
        last_status_print = current_time;
    }
    
    // Check for low memory condition
    if (ESP.getFreeHeap() < HEAP_WARNING_THRESHOLD) {
        Serial.printf("WARNING: Low memory! Free heap: %d bytes\n", ESP.getFreeHeap());
    }
    
    // Small delay to prevent watchdog issues
    delay(10);
}

void setupWiFi() {
    WiFi.mode(WIFI_STA);
    WiFi.setHostname(DEVICE_NAME);
    
    Serial.printf("Connecting to WiFi network: %s\n", WIFI_SSID);
    current_led_status = LED_BLINK_BLUE;
    
    wifi_connected = connectToWiFi();
    
    if (wifi_connected) {
        Serial.println("WiFi connected successfully!");
        Serial.printf("IP address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("Signal strength: %d dBm\n", WiFi.RSSI());
        current_led_status = LED_SOLID_BLUE;
    } else {
        Serial.println("ERROR: Failed to connect to WiFi");
        current_led_status = LED_SOLID_RED;
    }
}

bool connectToWiFi() {
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    unsigned long start_time = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start_time < WIFI_TIMEOUT_MS) {
        delay(500);
        Serial.print(".");
        
        // Blink LED during connection attempt
        static bool led_state = false;
        digitalWrite(STATUS_LED_PIN, led_state ? HIGH : LOW);
        led_state = !led_state;
    }
    Serial.println();
    
    return WiFi.status() == WL_CONNECTED;
}

void handleWiFiReconnection() {
    static unsigned long last_wifi_check = 0;
    unsigned long current_time = millis();
    
    // Check WiFi status every 10 seconds
    if (current_time - last_wifi_check >= 10000) {
        bool currently_connected = (WiFi.status() == WL_CONNECTED);
        
        if (wifi_connected && !currently_connected) {
            Serial.println("WiFi connection lost! Attempting to reconnect...");
            wifi_connected = false;
            current_led_status = LED_BLINK_BLUE;
            
            // Attempt reconnection
            wifi_connected = connectToWiFi();
            
            if (wifi_connected) {
                Serial.println("WiFi reconnected successfully!");
                current_led_status = LED_SOLID_BLUE;
                
                // Restart web server if it was stopped
                if (!webServer.isRunning()) {
                    webServer.begin();
                }
            } else {
                Serial.println("WiFi reconnection failed");
                current_led_status = LED_SOLID_RED;
            }
        } else if (!wifi_connected && currently_connected) {
            // WiFi came back online
            wifi_connected = true;
            Serial.println("WiFi connection restored!");
            current_led_status = LED_SOLID_BLUE;
            
            if (!webServer.isRunning()) {
                webServer.begin();
            }
        }
        
        last_wifi_check = current_time;
    }
}

void updateStatusLED() {
    static unsigned long last_led_update = 0;
    static bool led_state = false;
    unsigned long current_time = millis();
    
    switch (current_led_status) {
        case LED_OFF:
            digitalWrite(STATUS_LED_PIN, LOW);
            break;
            
        case LED_SOLID_BLUE:
        case LED_SOLID_GREEN:
        case LED_SOLID_RED:
            digitalWrite(STATUS_LED_PIN, HIGH);
            break;
            
        case LED_BLINK_BLUE:
        case LED_BLINK_RED:
            if (current_time - last_led_update >= LED_BLINK_INTERVAL_MS) {
                led_state = !led_state;
                digitalWrite(STATUS_LED_PIN, led_state ? HIGH : LOW);
                last_led_update = current_time;
            }
            break;
    }
}

void printSystemStatus() {
    Serial.println("\n" + String("-").repeat(40));
    Serial.println("📊 SYSTEM STATUS");
    Serial.println(String("-").repeat(40));
    
    // Uptime
    unsigned long uptime_ms = millis() - boot_time;
    unsigned long uptime_seconds = uptime_ms / 1000;
    unsigned long uptime_minutes = uptime_seconds / 60;
    unsigned long uptime_hours = uptime_minutes / 60;
    
    Serial.printf("⏱️  Uptime: %lu:%02lu:%02lu\n", 
                 uptime_hours, uptime_minutes % 60, uptime_seconds % 60);
    
    // Memory
    Serial.printf("💾 Free Heap: %d bytes\n", ESP.getFreeHeap());
    
    // WiFi status
    if (wifi_connected) {
        Serial.printf("📶 WiFi: Connected (%s, %d dBm)\n", 
                     WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        Serial.println("📶 WiFi: Disconnected");
    }
    
    // Web server status
    if (webServer.isRunning()) {
        Serial.printf("🌐 Web Server: Running (port %d)\n", HTTP_PORT);
        Serial.printf("   Last request: %lu ms ago\n", 
                     millis() - webServer.getLastRequestTime());
    } else {
        Serial.println("🌐 Web Server: Stopped");
    }
    
    // Sensor status
    Serial.printf("🌡️  Sensors: %s\n", sensorManager.getStatusString().c_str());
    
    if (sensorManager.isSHT45Connected()) {
        SensorReading sht45 = sensorManager.getSHT45Data();
        Serial.printf("   SHT45: %.2f°C, %.1f%%RH (errors: %d)\n", 
                     sht45.temperature, sht45.humidity, sht45.error_count);
    }
    
    if (sensorManager.isHDC3022Connected()) {
        SensorReading hdc3022 = sensorManager.getHDC3022Data();
        Serial.printf("   HDC3022: %.2f°C, %.1f%%RH (errors: %d)\n", 
                     hdc3022.temperature, hdc3022.humidity, hdc3022.error_count);
    }
    
    if (sensorManager.areAnySensorsConnected()) {
        Serial.printf("   Average: %.2f°C, %.1f%%RH\n", 
                     sensorManager.getAverageTemperature(), 
                     sensorManager.getAverageHumidity());
        Serial.printf("   Difference: %.2f°C, %.1f%%RH\n", 
                     sensorManager.getTemperatureDifference(), 
                     sensorManager.getHumidityDifference());
    }
    
    // System health
    SystemStatus system_status = sensorManager.getSystemStatus();
    String status_text;
    switch (system_status) {
        case SYSTEM_OK:
            status_text = "✅ OK";
            break;
        case SYSTEM_WIFI_DISCONNECTED:
            status_text = "⚠️  WiFi Disconnected";
            break;
        case SYSTEM_SENSOR_FAILURE:
            status_text = "❌ Sensor Failure";
            break;
        case SYSTEM_LOW_MEMORY:
            status_text = "⚠️  Low Memory";
            break;
        case SYSTEM_CRITICAL_ERROR:
            status_text = "🚨 Critical Error";
            break;
        default:
            status_text = "❓ Unknown";
            break;
    }
    
    Serial.printf("🔧 System Health: %s\n", status_text.c_str());
    Serial.println(String("-").repeat(40) + "\n");
}