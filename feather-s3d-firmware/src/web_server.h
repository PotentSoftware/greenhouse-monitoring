#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>
#include "config.h"
#include "sensor_manager.h"

class GreenhouseWebServer {
private:
    WebServer* server;
    bool server_started;
    unsigned long last_request_time;
    int active_connections;
    
    // Request handlers
    void handleRoot();
    void handleSensors();
    void handleStatus();
    void handleConfig();
    void handleNotFound();
    void handleCORS();
    
    // JSON response builders
    void buildSensorResponse(JsonDocument& doc);
    void buildStatusResponse(JsonDocument& doc);
    void buildConfigResponse(JsonDocument& doc);
    
    // Utility methods
    void sendJSONResponse(const JsonDocument& doc, int status_code = 200);
    void sendErrorResponse(const String& error, int status_code = 500);
    void logRequest(const String& method, const String& uri, int status_code);
    bool isValidRequest();
    
    // CORS handling
    void setCORSHeaders();
    bool handlePreflightRequest();
    
public:
    GreenhouseWebServer();
    ~GreenhouseWebServer();
    
    // Server lifecycle
    bool begin();
    void handle();
    void stop();
    
    // Status methods
    bool isRunning() const;
    int getActiveConnections() const;
    unsigned long getLastRequestTime() const;
    
    // Configuration
    void setPort(int port);
    void enableCORS(bool enable);
    
    // Statistics
    void printServerStats() const;
};

// Global web server instance
extern GreenhouseWebServer webServer;

#endif // WEB_SERVER_H