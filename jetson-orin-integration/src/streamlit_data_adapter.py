#!/usr/bin/env python3
"""
Data adapter for Streamlit dashboard to integrate with existing Jetson server
Maps sensor data from the greenhouse server to Streamlit format
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional
import numpy as np

class StreamlitDataAdapter:
    """Adapts data from Jetson greenhouse server for Streamlit dashboard"""
    
    def __init__(self, server_url="http://192.168.1.81:8080"):
        self.server_url = server_url
        self.logger = logging.getLogger(__name__)
    
    def get_sensor_data(self) -> Optional[Dict]:
        """
        Fetch sensor data from Jetson server and format for Streamlit
        
        Returns:
            Dict with keys: sht45_temp, hdc3022_temp, foliage_temp, 
                           sht45_humidity, hdc3022_humidity, air_vpd, enhanced_vpd
        """
        try:
            # Fetch data from ESP32-S3 sensor server
            response = requests.get(f"{self.server_url}/sensors", timeout=5)
            
            if response.status_code != 200:
                self.logger.warning(f"Server returned status {response.status_code}")
                return None
            
            raw_data = response.json()
            
            # Map the existing data structure to Streamlit format
            streamlit_data = self._map_sensor_data(raw_data)
            
            return streamlit_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch sensor data: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    def _map_sensor_data(self, raw_data: Dict) -> Dict:
        """
        Map raw sensor data to Streamlit format
        
        Expected raw data structure from existing server:
        {
            "sensors": {
                "feather_s3d": {
                    "sht45": {"temperature": float, "humidity": float},
                    "hdc3022": {"temperature": float, "humidity": float}
                },
                "thermal_camera": {...},
                "foliage_temperature": {"temperature": float}
            },
            "vpd": {
                "air_vpd": float,
                "enhanced_vpd": float
            }
        }
        """
        
        # Initialize with default values
        mapped_data = {
            'timestamp': datetime.now().isoformat(),
            'sht45_temp': 0.0,
            'hdc3022_temp': 0.0,
            'foliage_temp': 0.0,
            'sht45_humidity': 0.0,
            'hdc3022_humidity': 0.0,
            'air_vpd': 0.0,
            'enhanced_vpd': 0.0
        }
        
        try:
            # Map ESP32-S3 sensor data structure:
            # {"hdc3022": {"status": "ok", "humidity": 52.2, "temperature": 30.6}, 
            #  "sht45": {"status": "ok", "humidity": 47.6, "temperature": 30.3}, 
            #  "averages": {"vpd": 2.18, "humidity": 49.9, "temperature": 30.4}}
            
            # SHT45 data
            if 'sht45' in raw_data and raw_data['sht45'].get('status') == 'ok':
                mapped_data['sht45_temp'] = float(raw_data['sht45']['temperature'])
                mapped_data['sht45_humidity'] = float(raw_data['sht45']['humidity'])
            
            # HDC3022 data
            if 'hdc3022' in raw_data and raw_data['hdc3022'].get('status') == 'ok':
                mapped_data['hdc3022_temp'] = float(raw_data['hdc3022']['temperature'])
                mapped_data['hdc3022_humidity'] = float(raw_data['hdc3022']['humidity'])
            
            # VPD from averages
            if 'averages' in raw_data and 'vpd' in raw_data['averages']:
                mapped_data['air_vpd'] = float(raw_data['averages']['vpd'])
                # Calculate enhanced VPD
                mapped_data['enhanced_vpd'] = self._calculate_enhanced_vpd(
                    mapped_data['sht45_temp'],
                    mapped_data['sht45_humidity'],
                    mapped_data['sht45_temp']  # Use air temp as foliage temp fallback
                )
            
            # No foliage temperature from ESP32-S3, set to NaN
            mapped_data['foliage_temp'] = np.nan
            
            # Ensure all values are valid numbers
            for key, value in mapped_data.items():
                if key != 'timestamp':
                    if np.isnan(value) or np.isinf(value):
                        if key == 'foliage_temp':
                            mapped_data[key] = np.nan  # Keep NaN for invalid foliage temp
                        else:
                            mapped_data[key] = 0.0
            
            return mapped_data
            
        except Exception as e:
            self.logger.error(f"Error mapping sensor data: {e}")
            return mapped_data
    
    def _calculate_enhanced_vpd(self, air_temp: float, humidity: float, foliage_temp: float) -> float:
        """
        Calculate enhanced VPD using foliage temperature
        
        Args:
            air_temp: Air temperature in Celsius
            humidity: Relative humidity in percent
            foliage_temp: Foliage temperature in Celsius
            
        Returns:
            Enhanced VPD in kPa
        """
        try:
            if np.isnan(foliage_temp) or foliage_temp <= 0:
                # Fallback to air temperature if foliage temp is invalid
                foliage_temp = air_temp
            
            # Saturation vapor pressure at air temperature (kPa)
            es_air = 0.6108 * np.exp(17.27 * air_temp / (air_temp + 237.3))
            
            # Actual vapor pressure (kPa)
            ea = es_air * (humidity / 100.0)
            
            # Saturation vapor pressure at foliage temperature (kPa)
            es_foliage = 0.6108 * np.exp(17.27 * foliage_temp / (foliage_temp + 237.3))
            
            # Enhanced VPD using foliage temperature
            enhanced_vpd = es_foliage - ea
            
            return max(0.0, enhanced_vpd)
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced VPD: {e}")
            return 0.0
    
    def get_mock_data(self) -> Dict:
        """Generate mock data for testing when server is unavailable"""
        import random
        
        base_temp = 22.0
        base_humidity = 65.0
        
        # Generate realistic sensor variations
        sht45_temp = base_temp + random.uniform(-1.5, 2.0)
        hdc3022_temp = base_temp + random.uniform(-2.0, 1.5)
        
        # Foliage temperature - occasionally zero (invalid reading)
        if random.random() < 0.1:  # 10% chance of invalid reading
            foliage_temp = 0.0
        else:
            foliage_temp = base_temp + random.uniform(-2.0, 3.0)
        
        sht45_humidity = base_humidity + random.uniform(-8.0, 12.0)
        hdc3022_humidity = base_humidity + random.uniform(-6.0, 10.0)
        
        # Calculate VPD values
        air_vpd = 0.8 + random.uniform(-0.3, 0.5)
        enhanced_vpd = self._calculate_enhanced_vpd(sht45_temp, sht45_humidity, foliage_temp)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'sht45_temp': sht45_temp,
            'hdc3022_temp': hdc3022_temp,
            'foliage_temp': foliage_temp if foliage_temp > 0 else np.nan,
            'sht45_humidity': sht45_humidity,
            'hdc3022_humidity': hdc3022_humidity,
            'air_vpd': air_vpd,
            'enhanced_vpd': enhanced_vpd
        }

if __name__ == "__main__":
    # Test the adapter
    adapter = StreamlitDataAdapter()
    
    # Try to get real data
    data = adapter.get_sensor_data()
    
    if data:
        print("Real sensor data:")
        print(json.dumps(data, indent=2))
    else:
        print("Using mock data:")
        mock_data = adapter.get_mock_data()
        print(json.dumps(mock_data, indent=2))
