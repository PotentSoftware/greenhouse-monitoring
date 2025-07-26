#include "sensor_manager.h"

// Global instance
SensorManager sensorManager;

SensorManager::SensorManager() : 
    i2c1(nullptr),
    i2c2(nullptr),
    sht45_initialized(false),
    hdc3022_initialized(false),
    last_read_time(0),
    consecutive_errors(0),
    last_error_time(0) {
    
    // Initialize sensor data structures
    sht45_data = {0.0, 0.0, SENSOR_ERROR_NOT_CONNECTED, 0, 0, false};
    hdc3022_data = {0.0, 0.0, SENSOR_ERROR_NOT_CONNECTED, 0, 0, false};
}

SensorManager::~SensorManager() {
    if (i2c1) delete i2c1;
    if (i2c2) delete i2c2;
}

bool SensorManager::begin() {
    Serial.println("Initializing Sensor Manager...");
    
    // Initialize I2C buses
    i2c1 = new TwoWire(0);
    i2c2 = new TwoWire(1);
    
    // Configure I2C1 for SHT45 (LDO1)
    i2c1->begin(I2C1_SDA_PIN, I2C1_SCL_PIN, I2C_FREQ);
    
    // Configure I2C2 for HDC3022 (LDO2)  
    i2c2->begin(I2C2_SDA_PIN, I2C2_SCL_PIN, I2C_FREQ);
    
    delay(100); // Allow I2C buses to stabilize
    
    // Initialize sensors
    bool sht45_ok = initializeSHT45();
    bool hdc3022_ok = initializeHDC3022();
    
    if (sht45_ok || hdc3022_ok) {
        Serial.println("Sensor Manager initialized successfully");
        Serial.printf("SHT45: %s, HDC3022: %s\n", 
                     sht45_ok ? "OK" : "FAILED",
                     hdc3022_ok ? "OK" : "FAILED");
        return true;
    } else {
        Serial.println("ERROR: No sensors could be initialized!");
        return false;
    }
}

bool SensorManager::initializeSHT45() {
    Serial.println("Initializing SHT45 sensor...");
    
    if (!sht45.begin(SHT45_I2C_ADDRESS, i2c1)) {
        Serial.println("ERROR: Could not find SHT45 sensor");
        sht45_initialized = false;
        sht45_data.status = SENSOR_ERROR_NOT_CONNECTED;
        return false;
    }
    
    // Configure SHT45 settings
    sht45.setPrecision(SHT4X_HIGH_PRECISION);
    sht45.setHeater(SHT4X_NO_HEATER);
    
    sht45_initialized = true;
    sht45_data.status = SENSOR_OK;
    sht45_data.connected = true;
    
    Serial.println("SHT45 sensor initialized successfully");
    return true;
}

bool SensorManager::initializeHDC3022() {
    Serial.println("Initializing HDC3022 sensor...");
    
    if (!hdc3022.begin(HDC3022_I2C_ADDRESS, i2c2)) {
        Serial.println("ERROR: Could not find HDC3022 sensor");
        hdc3022_initialized = false;
        hdc3022_data.status = SENSOR_ERROR_NOT_CONNECTED;
        return false;
    }
    
    // Configure HDC3022 settings
    hdc3022.setMeasurementMode(HDC302X_CONTINUOUS_1HZ);
    hdc3022.configAutoMeasurementMode(HDC302X_AUTO_MEASUREMENT_ENABLE);
    
    hdc3022_initialized = true;
    hdc3022_data.status = SENSOR_OK;
    hdc3022_data.connected = true;
    
    Serial.println("HDC3022 sensor initialized successfully");
    return true;
}

bool SensorManager::readAllSensors() {
    bool success = false;
    
    // Read SHT45
    if (sht45_initialized) {
        SensorStatus sht45_status = readSHT45();
        if (sht45_status == SENSOR_OK) {
            success = true;
        }
    }
    
    // Read HDC3022
    if (hdc3022_initialized) {
        SensorStatus hdc3022_status = readHDC3022();
        if (hdc3022_status == SENSOR_OK) {
            success = true;
        }
    }
    
    last_read_time = millis();
    
    if (!success) {
        consecutive_errors++;
        last_error_time = millis();
        
        if (DEBUG_ENABLED) {
            Serial.printf("ERROR: All sensor reads failed (consecutive errors: %d)\n", consecutive_errors);
        }
    } else {
        consecutive_errors = 0;
    }
    
    return success;
}

SensorStatus SensorManager::readSHT45() {
    if (!sht45_initialized) {
        return SENSOR_ERROR_NOT_CONNECTED;
    }
    
    sensors_event_t humidity_event, temp_event;
    
    // Attempt to read sensor with timeout
    unsigned long start_time = millis();
    bool read_success = false;
    
    while (millis() - start_time < SENSOR_TIMEOUT_MS) {
        if (sht45.getEvent(&humidity_event, &temp_event)) {
            read_success = true;
            break;
        }
        delay(10);
    }
    
    if (!read_success) {
        updateSensorStatus(sht45_data, SENSOR_ERROR_TIMEOUT);
        return SENSOR_ERROR_TIMEOUT;
    }
    
    float temperature = temp_event.temperature + SHT45_TEMP_OFFSET;
    float humidity = humidity_event.relative_humidity + SHT45_HUMIDITY_OFFSET;
    
    // Validate readings
    if (!isValidTemperature(temperature) || !isValidHumidity(humidity)) {
        updateSensorStatus(sht45_data, SENSOR_ERROR_INVALID_DATA);
        return SENSOR_ERROR_INVALID_DATA;
    }
    
    // Update sensor data
    sht45_data.temperature = temperature;
    sht45_data.humidity = humidity;
    sht45_data.last_read_time = millis();
    updateSensorStatus(sht45_data, SENSOR_OK);
    
    if (DEBUG_SENSOR_READINGS) {
        Serial.printf("SHT45: %.2f°C, %.2f%%RH\n", temperature, humidity);
    }
    
    return SENSOR_OK;
}

SensorStatus SensorManager::readHDC3022() {
    if (!hdc3022_initialized) {
        return SENSOR_ERROR_NOT_CONNECTED;
    }
    
    sensors_event_t humidity_event, temp_event;
    
    // Attempt to read sensor with timeout
    unsigned long start_time = millis();
    bool read_success = false;
    
    while (millis() - start_time < SENSOR_TIMEOUT_MS) {
        if (hdc3022.getEvent(&humidity_event, &temp_event)) {
            read_success = true;
            break;
        }
        delay(10);
    }
    
    if (!read_success) {
        updateSensorStatus(hdc3022_data, SENSOR_ERROR_TIMEOUT);
        return SENSOR_ERROR_TIMEOUT;
    }
    
    float temperature = temp_event.temperature + HDC3022_TEMP_OFFSET;
    float humidity = humidity_event.relative_humidity + HDC3022_HUMIDITY_OFFSET;
    
    // Validate readings
    if (!isValidTemperature(temperature) || !isValidHumidity(humidity)) {
        updateSensorStatus(hdc3022_data, SENSOR_ERROR_INVALID_DATA);
        return SENSOR_ERROR_INVALID_DATA;
    }
    
    // Update sensor data
    hdc3022_data.temperature = temperature;
    hdc3022_data.humidity = humidity;
    hdc3022_data.last_read_time = millis();
    updateSensorStatus(hdc3022_data, SENSOR_OK);
    
    if (DEBUG_SENSOR_READINGS) {
        Serial.printf("HDC3022: %.2f°C, %.2f%%RH\n", temperature, humidity);
    }
    
    return SENSOR_OK;
}

void SensorManager::updateSensorStatus(SensorReading& sensor, SensorStatus status) {
    if (status != SENSOR_OK) {
        sensor.error_count++;
        if (sensor.error_count >= SENSOR_ERROR_THRESHOLD) {
            sensor.connected = false;
        }
    } else {
        // Reset error count on successful read
        if (sensor.error_count > 0) {
            sensor.error_count = max(0, sensor.error_count - 1);
        }
        sensor.connected = true;
    }
    
    sensor.status = status;
}

bool SensorManager::isValidTemperature(float temp) {
    return (temp >= -40.0 && temp <= 85.0); // Reasonable temperature range
}

bool SensorManager::isValidHumidity(float humidity) {
    return (humidity >= 0.0 && humidity <= 100.0); // Valid humidity range
}

// Data access methods
SensorReading SensorManager::getSHT45Data() const {
    return sht45_data;
}

SensorReading SensorManager::getHDC3022Data() const {
    return hdc3022_data;
}

bool SensorManager::isSHT45Connected() const {
    return sht45_initialized && sht45_data.connected;
}

bool SensorManager::isHDC3022Connected() const {
    return hdc3022_initialized && hdc3022_data.connected;
}

bool SensorManager::areAnySensorsConnected() const {
    return isSHT45Connected() || isHDC3022Connected();
}

float SensorManager::getAverageTemperature() const {
    float total = 0.0;
    int count = 0;
    
    if (isSHT45Connected() && sht45_data.status == SENSOR_OK) {
        total += sht45_data.temperature;
        count++;
    }
    
    if (isHDC3022Connected() && hdc3022_data.status == SENSOR_OK) {
        total += hdc3022_data.temperature;
        count++;
    }
    
    return (count > 0) ? (total / count) : 0.0;
}

float SensorManager::getAverageHumidity() const {
    float total = 0.0;
    int count = 0;
    
    if (isSHT45Connected() && sht45_data.status == SENSOR_OK) {
        total += sht45_data.humidity;
        count++;
    }
    
    if (isHDC3022Connected() && hdc3022_data.status == SENSOR_OK) {
        total += hdc3022_data.humidity;
        count++;
    }
    
    return (count > 0) ? (total / count) : 0.0;
}

float SensorManager::getTemperatureDifference() const {
    if (isSHT45Connected() && isHDC3022Connected() && 
        sht45_data.status == SENSOR_OK && hdc3022_data.status == SENSOR_OK) {
        return abs(sht45_data.temperature - hdc3022_data.temperature);
    }
    return 0.0;
}

float SensorManager::getHumidityDifference() const {
    if (isSHT45Connected() && isHDC3022Connected() && 
        sht45_data.status == SENSOR_OK && hdc3022_data.status == SENSOR_OK) {
        return abs(sht45_data.humidity - hdc3022_data.humidity);
    }
    return 0.0;
}

SystemStatus SensorManager::getSystemStatus() const {
    if (!areAnySensorsConnected()) {
        return SYSTEM_SENSOR_FAILURE;
    }
    
    if (consecutive_errors >= SENSOR_ERROR_THRESHOLD) {
        return SYSTEM_SENSOR_FAILURE;
    }
    
    return SYSTEM_OK;
}

int SensorManager::getTotalErrorCount() const {
    return sht45_data.error_count + hdc3022_data.error_count;
}

unsigned long SensorManager::getLastReadTime() const {
    return last_read_time;
}

String SensorManager::getStatusString() const {
    String status = "Sensors: ";
    
    if (isSHT45Connected()) {
        status += "SHT45:OK ";
    } else {
        status += "SHT45:FAIL ";
    }
    
    if (isHDC3022Connected()) {
        status += "HDC3022:OK";
    } else {
        status += "HDC3022:FAIL";
    }
    
    return status;
}

void SensorManager::setSHT45Offsets(float temp_offset, float humidity_offset) {
    // Note: In a real implementation, these would be stored in EEPROM/preferences
    Serial.printf("SHT45 offsets set: Temp=%.2f°C, Humidity=%.2f%%\n", temp_offset, humidity_offset);
}

void SensorManager::setHDC3022Offsets(float temp_offset, float humidity_offset) {
    // Note: In a real implementation, these would be stored in EEPROM/preferences
    Serial.printf("HDC3022 offsets set: Temp=%.2f°C, Humidity=%.2f%%\n", temp_offset, humidity_offset);
}

void SensorManager::printDiagnostics() const {
    Serial.println("=== Sensor Manager Diagnostics ===");
    Serial.printf("SHT45: %s, Errors: %d, Last Read: %lu\n", 
                 isSHT45Connected() ? "Connected" : "Disconnected",
                 sht45_data.error_count, sht45_data.last_read_time);
    Serial.printf("HDC3022: %s, Errors: %d, Last Read: %lu\n", 
                 isHDC3022Connected() ? "Connected" : "Disconnected",
                 hdc3022_data.error_count, hdc3022_data.last_read_time);
    Serial.printf("Consecutive Errors: %d, Last Error: %lu\n", consecutive_errors, last_error_time);
    Serial.printf("System Status: %d\n", getSystemStatus());
    Serial.println("================================");
}

bool SensorManager::performSelfTest() {
    Serial.println("Performing sensor self-test...");
    
    bool test_passed = true;
    
    // Test SHT45
    if (sht45_initialized) {
        if (readSHT45() != SENSOR_OK) {
            Serial.println("SHT45 self-test FAILED");
            test_passed = false;
        } else {
            Serial.println("SHT45 self-test PASSED");
        }
    }
    
    // Test HDC3022
    if (hdc3022_initialized) {
        if (readHDC3022() != SENSOR_OK) {
            Serial.println("HDC3022 self-test FAILED");
            test_passed = false;
        } else {
            Serial.println("HDC3022 self-test PASSED");
        }
    }
    
    Serial.printf("Self-test result: %s\n", test_passed ? "PASSED" : "FAILED");
    return test_passed;
}

void SensorManager::reset() {
    Serial.println("Resetting Sensor Manager...");
    
    sht45_initialized = false;
    hdc3022_initialized = false;
    consecutive_errors = 0;
    last_error_time = 0;
    
    // Reset sensor data
    sht45_data = {0.0, 0.0, SENSOR_ERROR_NOT_CONNECTED, 0, 0, false};
    hdc3022_data = {0.0, 0.0, SENSOR_ERROR_NOT_CONNECTED, 0, 0, false};
    
    // Reinitialize
    begin();
}