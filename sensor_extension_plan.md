# Sensor Extension Plan: EC and Nutrient Temperature

## Overview
Extending the greenhouse monitoring system to include:
- **Electrical Conductivity (EC)** - Nutrient solution strength
- **Nutrient Temperature** - Solution temperature for optimal uptake

## Hardware Requirements

### EC Sensor Options
1. **Atlas Scientific EZO-EC** (Recommended)
   - I2C interface (compatible with existing setup)
   - Auto-calibration capability
   - Temperature compensation
   - Cost: ~$45

2. **DFRobot Gravity EC Sensor**
   - Analog output
   - Lower cost option: ~$25
   - Manual calibration required

### Temperature Sensor for Nutrient Solution
1. **DS18B20 Waterproof** (Recommended)
   - 1-Wire interface
   - Stainless steel probe
   - High accuracy: ±0.5°C
   - Cost: ~$10

2. **Atlas Scientific EZO-RTD**
   - I2C interface
   - Industrial grade
   - Cost: ~$45

## Integration Strategy

### BeagleConnect Freedom Integration
```python
# Add to ph_web_server.py

import board
import busio
from adafruit_ds18x20 import DS18X20
from adafruit_onewire.bus import OneWireBus

# EC sensor (Atlas Scientific EZO-EC via I2C)
def read_ec_sensor():
    try:
        # I2C communication with EZO-EC
        # Return EC value in μS/cm or ppm
        return ec_value
    except Exception as e:
        logging.error(f"EC sensor error: {e}")
        return None

# Nutrient temperature sensor (DS18B20)
def read_nutrient_temp():
    try:
        # 1-Wire communication
        return temp_celsius
    except Exception as e:
        logging.error(f"Nutrient temp sensor error: {e}")
        return None

# Enhanced sensor reading function
def get_all_sensor_data():
    return {
        'ph': read_ph_sensor(),
        'ec': read_ec_sensor(),
        'nutrient_temp': read_nutrient_temp(),
        'air_temp': read_air_temp(),
        'humidity': read_humidity(),
        'timestamp': datetime.now().isoformat()
    }
```

### Node-RED Flow Extensions

#### New Calculations
```javascript
// Enhanced nutrient monitoring
const nutrient_data = {
    ec: msg.payload.ec,
    nutrient_temp: msg.payload.nutrient_temp,
    ph: msg.payload.ph,
    
    // Derived metrics
    nutrient_strength: classify_ec(msg.payload.ec),
    temp_optimal: check_temp_range(msg.payload.nutrient_temp),
    nutrient_uptake_efficiency: calculate_uptake_efficiency(
        msg.payload.ec, 
        msg.payload.nutrient_temp, 
        msg.payload.ph
    )
};

function classify_ec(ec_value) {
    // μS/cm ranges for different crops
    if (ec_value < 800) return "Low";
    if (ec_value < 1200) return "Optimal_Leafy";
    if (ec_value < 2000) return "Optimal_Fruiting"; 
    return "High";
}

function calculate_uptake_efficiency(ec, temp, ph) {
    // Optimal ranges: pH 5.5-6.5, temp 18-22°C
    let ph_factor = 1 - Math.abs(6.0 - ph) * 0.2;
    let temp_factor = 1 - Math.abs(20 - temp) * 0.05;
    return Math.max(0, ph_factor * temp_factor);
}
```

## Database Schema Extensions

### InfluxDB Measurements
```
measurement: nutrients
├── fields:
│   ├── ec_value (float) - μS/cm
│   ├── nutrient_temp (float) - °C  
│   ├── uptake_efficiency (float) - 0-1
│   └── nutrient_strength (string) - classification
├── tags:
│   ├── location: greenhouse
│   ├── sensor_type: ec/temperature
│   └── solution_type: nutrient/water
```

## Grafana Dashboard Additions

### New Panels
1. **EC Trend Chart** - Historical nutrient strength
2. **Nutrient Temperature vs Air Temperature** - Comparison
3. **Uptake Efficiency Gauge** - Real-time optimization metric
4. **Alert Panel** - EC/temp out of range warnings

### Alert Rules
```yaml
EC_High:
  condition: ec_value > 2500
  message: "EC too high - dilute nutrient solution"

EC_Low:  
  condition: ec_value < 500
  message: "EC too low - add nutrients"

Nutrient_Temp_High:
  condition: nutrient_temp > 25
  message: "Nutrient temperature too high - add cooling"

Nutrient_Temp_Low:
  condition: nutrient_temp < 15  
  message: "Nutrient temperature too low - add heating"
```

## Implementation Timeline

### Phase 1: Hardware Setup (Week 1)
- [ ] Order sensors (EC + DS18B20)
- [ ] Install on BeagleConnect Freedom
- [ ] Test sensor readings

### Phase 2: Software Integration (Week 2)  
- [ ] Update BeaglePlay ph_web_server.py
- [ ] Add sensor reading functions
- [ ] Test data collection

### Phase 3: Dashboard Extension (Week 3)
- [ ] Update Node-RED flows
- [ ] Add new calculations
- [ ] Update Grafana dashboard
- [ ] Set up alerts

### Phase 4: Optimization (Week 4)
- [ ] Calibrate sensors
- [ ] Fine-tune alert thresholds  
- [ ] Add automated recommendations
- [ ] Performance testing

## Cost Estimate
- Atlas Scientific EZO-EC: $45
- DS18B20 Waterproof: $10  
- Connector cables: $10
- **Total: ~$65**

## Benefits
1. **Complete Nutrient Monitoring** - EC, pH, temperature
2. **Automated Optimization** - Real-time efficiency calculations
3. **Predictive Maintenance** - Early warning system
4. **Better Yields** - Optimal nutrient uptake conditions
5. **Cost Savings** - Prevent nutrient waste

## Future Extensions
- **Nutrient dosing pumps** - Automated adjustment
- **Multiple zones** - Different crop requirements
- **Machine learning** - Predictive nutrient scheduling
- **Mobile notifications** - Critical alerts
