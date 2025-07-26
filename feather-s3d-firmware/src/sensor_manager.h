#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SHT4x.h>
#include <Adafruit_HDC302x.h>
#include "config.h"

class SensorManager {
private:
    // I2C instances
    TwoWire* i2c1;
    TwoWire* i2c2;
    
    // Sensor instances
    Adafruit_SHT4x sht45;
    Adafruit_HDC302x hdc3022;
    
    // Sensor data
    SensorReading sht45_data;
    SensorReading hdc3022_data;
    
    // Internal state
    bool sht45_initialized;
    bool hdc3022_initialized;
    unsigned long last_read_time;
    
    // Error tracking
    int consecutive_errors;
    unsigned long last_error_time;
    
    // Private methods
    bool initializeSHT45();
    bool initializeHDC3022();
    SensorStatus readSHT45();
    SensorStatus readHDC3022();
    void updateSensorStatus(SensorReading& sensor, SensorStatus status);
    bool isValidTemperature(float temp);
    bool isValidHumidity(float humidity);
    
public:
    SensorManager();
    ~SensorManager();
    
    // Initialization
    bool begin();
    void reset();
    
    // Sensor operations
    bool readAllSensors();
    bool readSHT45Only();
    bool readHDC3022Only();
    
    // Data access
    SensorReading getSHT45Data() const;
    SensorReading getHDC3022Data() const;
    bool isSHT45Connected() const;
    bool isHDC3022Connected() const;
    bool areAnySensorsConnected() const;
    
    // Averaged data (combining both sensors)
    float getAverageTemperature() const;
    float getAverageHumidity() const;
    float getTemperatureDifference() const;
    float getHumidityDifference() const;
    
    // Status and diagnostics
    SystemStatus getSystemStatus() const;
    int getTotalErrorCount() const;
    unsigned long getLastReadTime() const;
    String getStatusString() const;
    
    // Calibration (if needed)
    void setSHT45Offsets(float temp_offset, float humidity_offset);
    void setHDC3022Offsets(float temp_offset, float humidity_offset);
    
    // Utility methods
    void printDiagnostics() const;
    bool performSelfTest();
};

// Global sensor manager instance
extern SensorManager sensorManager;

#endif // SENSOR_MANAGER_H