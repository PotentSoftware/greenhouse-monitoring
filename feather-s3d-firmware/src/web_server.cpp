#include "web_server.h"

// Global instance
GreenhouseWebServer webServer;

GreenhouseWebServer::GreenhouseWebServer() : 
    server(nullptr),
    server_started(false),
    last_request_time(0),
    active_connections(0) {
}

GreenhouseWebServer::~GreenhouseWebServer() {
    stop();
    if (server) {
        delete server;
    }
}

bool GreenhouseWebServer::begin() {
    Serial.println("Starting web server...");
    
    if (server) {
        delete server;
    }
    
    server = new WebServer(HTTP_PORT);
    
    // Configure request handlers
    server->on("/", HTTP_GET, [this]() { handleRoot(); });
    server->on("/api/sensors", HTTP_GET, [this]() { handleSensors(); });
    server->on("/api/status", HTTP_GET, [this]() { handleStatus(); });
    server->on("/api/config", HTTP_GET, [this]() { handleConfig(); });
    
    // Handle CORS preflight requests
    server->on("/api/sensors", HTTP_OPTIONS, [this]() { handleCORS(); });
    server->on("/api/status", HTTP_OPTIONS, [this]() { handleCORS(); });
    server->on("/api/config", HTTP_OPTIONS, [this]() { handleCORS(); });
    
    // 404 handler
    server->onNotFound([this]() { handleNotFound(); });
    
    // Start server
    server->begin();
    server_started = true;
    
    // Setup mDNS if enabled
    if (strlen(MDNS_NAME) > 0) {
        if (MDNS.begin(MDNS_NAME)) {
            MDNS.addService("http", "tcp", HTTP_PORT);
            Serial.printf("mDNS responder started: %s.local\n", MDNS_NAME);
        } else {
            Serial.println("Error setting up mDNS responder!");
        }
    }
    
    Serial.printf("Web server started on port %d\n", HTTP_PORT);
    Serial.printf("Access URLs:\n");
    Serial.printf("  http://%s/\n", WiFi.localIP().toString().c_str());
    Serial.printf("  http://%s/api/sensors\n", WiFi.localIP().toString().c_str());
    Serial.printf("  http://%s/api/status\n", WiFi.localIP().toString().c_str());
    
    if (strlen(MDNS_NAME) > 0) {
        Serial.printf("  http://%s.local/\n", MDNS_NAME);
    }
    
    return true;
}

void GreenhouseWebServer::handle() {
    if (server && server_started) {
        server->handleClient();
        
        if (strlen(MDNS_NAME) > 0) {
            MDNS.update();
        }
    }
}

void GreenhouseWebServer::stop() {
    if (server && server_started) {
        server->stop();
        server_started = false;
        Serial.println("Web server stopped");
    }
}

void GreenhouseWebServer::handleRoot() {
    if (DEBUG_HTTP_REQUESTS) {
        Serial.println("Handling root request");
    }
    
    setCORSHeaders();
    
    String html = R"(
<!DOCTYPE html>
<html>
<head>
    <title>Feather S3[D] Precision Sensors</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        .sensor-card { background: #ecf0f1; padding: 20px; margin: 15px 0; border-radius: 8px; }
        .sensor-title { font-weight: bold; color: #34495e; margin-bottom: 10px; }
        .sensor-data { font-size: 18px; margin: 5px 0; }
        .status-ok { color: #27ae60; }
        .status-error { color: #e74c3c; }
        .api-links { margin-top: 30px; }
        .api-link { display: block; margin: 10px 0; padding: 10px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; text-align: center; }
        .api-link:hover { background: #2980b9; }
        .refresh-btn { background: #2ecc71; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 10px 0; }
        .refresh-btn:hover { background: #27ae60; }
    </style>
    <script>
        function refreshData() {
            fetch('/api/sensors')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('sht45-temp').textContent = data.sht45.temperature.toFixed(2) + '°C';
                    document.getElementById('sht45-humidity').textContent = data.sht45.humidity.toFixed(1) + '%';
                    document.getElementById('sht45-status').textContent = data.sht45.status;
                    document.getElementById('sht45-status').className = data.sht45.status === 'ok' ? 'status-ok' : 'status-error';
                    
                    document.getElementById('hdc3022-temp').textContent = data.hdc3022.temperature.toFixed(2) + '°C';
                    document.getElementById('hdc3022-humidity').textContent = data.hdc3022.humidity.toFixed(1) + '%';
                    document.getElementById('hdc3022-status').textContent = data.hdc3022.status;
                    document.getElementById('hdc3022-status').className = data.hdc3022.status === 'ok' ? 'status-ok' : 'status-error';
                    
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching sensor data:', error);
                });
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <h1>🌱 Feather S3[D] Precision Sensors</h1>
        
        <div class="sensor-card">
            <div class="sensor-title">SHT45 Sensor (I2C1)</div>
            <div class="sensor-data">Temperature: <span id="sht45-temp">--</span></div>
            <div class="sensor-data">Humidity: <span id="sht45-humidity">--</span></div>
            <div class="sensor-data">Status: <span id="sht45-status" class="status-ok">--</span></div>
        </div>
        
        <div class="sensor-card">
            <div class="sensor-title">HDC3022 Sensor (I2C2)</div>
            <div class="sensor-data">Temperature: <span id="hdc3022-temp">--</span></div>
            <div class="sensor-data">Humidity: <span id="hdc3022-humidity">--</span></div>
            <div class="sensor-data">Status: <span id="hdc3022-status" class="status-ok">--</span></div>
        </div>
        
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        <div>Last Update: <span id="last-update">--</span></div>
        
        <div class="api-links">
            <h3>API Endpoints</h3>
            <a href="/api/sensors" class="api-link">📊 Sensor Data (JSON)</a>
            <a href="/api/status" class="api-link">⚙️ System Status</a>
            <a href="/api/config" class="api-link">🔧 Configuration</a>
        </div>
    </div>
</body>
</html>
    )";
    
    server->send(200, "text/html", html);
    logRequest("GET", "/", 200);
}

void GreenhouseWebServer::handleSensors() {
    if (DEBUG_HTTP_REQUESTS) {
        Serial.println("Handling /api/sensors request");
    }
    
    setCORSHeaders();
    
    JsonDocument doc;
    buildSensorResponse(doc);
    sendJSONResponse(doc);
    
    logRequest("GET", "/api/sensors", 200);
}

void GreenhouseWebServer::handleStatus() {
    if (DEBUG_HTTP_REQUESTS) {
        Serial.println("Handling /api/status request");
    }
    
    setCORSHeaders();
    
    JsonDocument doc;
    buildStatusResponse(doc);
    sendJSONResponse(doc);
    
    logRequest("GET", "/api/status", 200);
}

void GreenhouseWebServer::handleConfig() {
    if (DEBUG_HTTP_REQUESTS) {
        Serial.println("Handling /api/config request");
    }
    
    setCORSHeaders();
    
    JsonDocument doc;
    buildConfigResponse(doc);
    sendJSONResponse(doc);
    
    logRequest("GET", "/api/config", 200);
}

void GreenhouseWebServer::handleCORS() {
    setCORSHeaders();
    server->send(200, "text/plain", "");
    logRequest("OPTIONS", server->uri(), 200);
}

void GreenhouseWebServer::handleNotFound() {
    setCORSHeaders();
    
    JsonDocument doc;
    doc["error"] = "Not Found";
    doc["message"] = "The requested endpoint does not exist";
    doc["available_endpoints"] = JsonArray();
    doc["available_endpoints"].add("/");
    doc["available_endpoints"].add("/api/sensors");
    doc["available_endpoints"].add("/api/status");
    doc["available_endpoints"].add("/api/config");
    
    sendJSONResponse(doc, 404);
    logRequest(server->method() == HTTP_GET ? "GET" : "POST", server->uri(), 404);
}

void GreenhouseWebServer::buildSensorResponse(JsonDocument& doc) {
    SensorReading sht45_data = sensorManager.getSHT45Data();
    SensorReading hdc3022_data = sensorManager.getHDC3022Data();
    
    // SHT45 data
    JsonObject sht45 = doc["sht45"].to<JsonObject>();
    sht45["temperature"] = round(sht45_data.temperature * 100.0) / 100.0; // Round to 2 decimal places
    sht45["humidity"] = round(sht45_data.humidity * 10.0) / 10.0; // Round to 1 decimal place
    sht45["status"] = (sht45_data.status == SENSOR_OK) ? "ok" : "error";
    sht45["last_read"] = sht45_data.last_read_time;
    sht45["error_count"] = sht45_data.error_count;
    sht45["connected"] = sht45_data.connected;
    
    // HDC3022 data
    JsonObject hdc3022 = doc["hdc3022"].to<JsonObject>();
    hdc3022["temperature"] = round(hdc3022_data.temperature * 100.0) / 100.0;
    hdc3022["humidity"] = round(hdc3022_data.humidity * 10.0) / 10.0;
    hdc3022["status"] = (hdc3022_data.status == SENSOR_OK) ? "ok" : "error";
    hdc3022["last_read"] = hdc3022_data.last_read_time;
    hdc3022["error_count"] = hdc3022_data.error_count;
    hdc3022["connected"] = hdc3022_data.connected;
    
    // Averaged data (for convenience)
    JsonObject averaged = doc["averaged"].to<JsonObject>();
    averaged["temperature"] = round(sensorManager.getAverageTemperature() * 100.0) / 100.0;
    averaged["humidity"] = round(sensorManager.getAverageHumidity() * 10.0) / 10.0;
    averaged["temperature_difference"] = round(sensorManager.getTemperatureDifference() * 100.0) / 100.0;
    averaged["humidity_difference"] = round(sensorManager.getHumidityDifference() * 10.0) / 10.0;
    
    // System info
    JsonObject system = doc["system"].to<JsonObject>();
    system["uptime"] = millis();
    system["free_heap"] = ESP.getFreeHeap();
    system["wifi_rssi"] = WiFi.RSSI();
    system["timestamp"] = millis(); // In a real implementation, use NTP time
}

void GreenhouseWebServer::buildStatusResponse(JsonDocument& doc) {
    // System information
    JsonObject system = doc["system"].to<JsonObject>();
    system["version"] = FIRMWARE_VERSION;
    system["device_name"] = DEVICE_NAME;
    system["uptime"] = millis();
    system["free_heap"] = ESP.getFreeHeap();
    system["wifi_connected"] = WiFi.status() == WL_CONNECTED;
    system["wifi_rssi"] = WiFi.RSSI();
    system["ip_address"] = WiFi.localIP().toString();
    system["mac_address"] = WiFi.macAddress();
    
    // Sensor status
    JsonObject sensors = doc["sensors"].to<JsonObject>();
    
    JsonObject sht45_status = sensors["sht45"].to<JsonObject>();
    sht45_status["connected"] = sensorManager.isSHT45Connected();
    sht45_status["last_successful_read"] = sensorManager.getSHT45Data().last_read_time;
    sht45_status["error_count"] = sensorManager.getSHT45Data().error_count;
    
    JsonObject hdc3022_status = sensors["hdc3022"].to<JsonObject>();
    hdc3022_status["connected"] = sensorManager.isHDC3022Connected();
    hdc3022_status["last_successful_read"] = sensorManager.getHDC3022Data().last_read_time;
    hdc3022_status["error_count"] = sensorManager.getHDC3022Data().error_count;
    
    // Overall system status
    doc["overall_status"] = sensorManager.areAnySensorsConnected() ? "ok" : "error";
    doc["status_message"] = sensorManager.getStatusString();
}

void GreenhouseWebServer::buildConfigResponse(JsonDocument& doc) {
    // WiFi configuration
    JsonObject wifi = doc["wifi"].to<JsonObject>();
    wifi["ssid"] = WiFi.SSID();
    wifi["connected"] = WiFi.status() == WL_CONNECTED;
    wifi["ip_address"] = WiFi.localIP().toString();
    wifi["rssi"] = WiFi.RSSI();
    
    // Sensor configuration
    JsonObject sensors = doc["sensors"].to<JsonObject>();
    sensors["read_interval"] = SENSOR_READ_INTERVAL_MS;
    sensors["retry_count"] = SENSOR_RETRY_COUNT;
    sensors["timeout_ms"] = SENSOR_TIMEOUT_MS;
    
    // Server configuration
    JsonObject server_config = doc["server"].to<JsonObject>();
    server_config["port"] = HTTP_PORT;
    server_config["cors_enabled"] = CORS_ENABLED;
    server_config["mdns_name"] = MDNS_NAME;
    
    // Hardware configuration
    JsonObject hardware = doc["hardware"].to<JsonObject>();
    hardware["i2c1_sda"] = I2C1_SDA_PIN;
    hardware["i2c1_scl"] = I2C1_SCL_PIN;
    hardware["i2c2_sda"] = I2C2_SDA_PIN;
    hardware["i2c2_scl"] = I2C2_SCL_PIN;
    hardware["status_led"] = STATUS_LED_PIN;
}

void GreenhouseWebServer::sendJSONResponse(const JsonDocument& doc, int status_code) {
    String response;
    serializeJson(doc, response);
    
    server->send(status_code, "application/json", response);
    last_request_time = millis();
}

void GreenhouseWebServer::sendErrorResponse(const String& error, int status_code) {
    JsonDocument doc;
    doc["error"] = error;
    doc["timestamp"] = millis();
    
    sendJSONResponse(doc, status_code);
}

void GreenhouseWebServer::setCORSHeaders() {
    if (CORS_ENABLED) {
        server->sendHeader("Access-Control-Allow-Origin", "*");
        server->sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        server->sendHeader("Access-Control-Allow-Headers", "Content-Type");
    }
}

void GreenhouseWebServer::logRequest(const String& method, const String& uri, int status_code) {
    if (DEBUG_HTTP_REQUESTS) {
        Serial.printf("[%lu] %s %s -> %d\n", millis(), method.c_str(), uri.c_str(), status_code);
    }
}

bool GreenhouseWebServer::isRunning() const {
    return server_started && server != nullptr;
}

int GreenhouseWebServer::getActiveConnections() const {
    return active_connections;
}

unsigned long GreenhouseWebServer::getLastRequestTime() const {
    return last_request_time;
}

void GreenhouseWebServer::printServerStats() const {
    Serial.println("=== Web Server Statistics ===");
    Serial.printf("Status: %s\n", isRunning() ? "Running" : "Stopped");
    Serial.printf("Port: %d\n", HTTP_PORT);
    Serial.printf("Active Connections: %d\n", active_connections);
    Serial.printf("Last Request: %lu ms ago\n", millis() - last_request_time);
    Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
    Serial.println("=============================");
}