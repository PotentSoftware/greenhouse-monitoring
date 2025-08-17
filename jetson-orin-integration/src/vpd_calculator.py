#!/usr/bin/env python3
"""
VPD Calculator for Jetson Orin Nano
Calculates various VPD types using thermal and precision sensor data
"""

import math
import logging
from typing import Dict, Optional

class VPDCalculator:
    def __init__(self):
        logging.info("🧮 VPD Calculator initialized")
    
    def calculate_svp(self, temperature: float) -> float:
        """Calculate Saturation Vapor Pressure using Tetens equation"""
        if temperature is None:
            return None
        return 0.6108 * math.exp(17.27 * temperature / (temperature + 237.3))
    
    def calculate_vpd(self, temperature: float, humidity: float) -> float:
        """Calculate VPD from temperature and humidity"""
        if temperature is None or humidity is None:
            return None
        
        svp = self.calculate_svp(temperature)
        avp = svp * (humidity / 100.0)
        vpd = svp - avp
        return round(vpd, 3)
    
    def calculate_all_vpd_types(self, sensor_data: Dict) -> Dict:
        """Calculate all VPD types from sensor data"""
        try:
            # Get air temperature and humidity from Feather S3[D]
            air_temp = sensor_data["feather_s3d"]["averages"].get("temperature")
            air_humidity = sensor_data["feather_s3d"]["averages"].get("humidity")
            
            # Get individual sensor data
            sht45_temp = sensor_data["feather_s3d"]["sht45"].get("temperature")
            sht45_humidity = sensor_data["feather_s3d"]["sht45"].get("humidity")
            hdc3022_temp = sensor_data["feather_s3d"]["hdc3022"].get("temperature")
            hdc3022_humidity = sensor_data["feather_s3d"]["hdc3022"].get("humidity")
            
            # Get thermal camera temperatures
            thermal_min = sensor_data["thermal_camera"].get("min_temp")
            thermal_max = sensor_data["thermal_camera"].get("max_temp")
            thermal_avg = sensor_data["thermal_camera"].get("avg_temp")
            thermal_modal = sensor_data["thermal_camera"].get("modal_temp")
            thermal_median = sensor_data["thermal_camera"].get("median_temp")
            
            vpd_results = {}
            
            # Standard Air VPD (using averaged air temperature and humidity)
            vpd_results["air_vpd"] = self.calculate_vpd(air_temp, air_humidity)
            
            # Individual sensor VPDs
            vpd_results["sht45_vpd"] = self.calculate_vpd(sht45_temp, sht45_humidity)
            vpd_results["hdc3022_vpd"] = self.calculate_vpd(hdc3022_temp, hdc3022_humidity)
            
            # Canopy VPD calculations (thermal temperature + air humidity)
            if air_humidity is not None:
                vpd_results["canopy_vpd_min"] = self.calculate_vpd(thermal_min, air_humidity)
                vpd_results["canopy_vpd_max"] = self.calculate_vpd(thermal_max, air_humidity)
                vpd_results["canopy_vpd_avg"] = self.calculate_vpd(thermal_avg, air_humidity)
                vpd_results["canopy_vpd_modal"] = self.calculate_vpd(thermal_modal, air_humidity)
                vpd_results["canopy_vpd_median"] = self.calculate_vpd(thermal_median, air_humidity)
            
            # Enhanced VPD with individual sensor humidity
            vpd_results["enhanced_vpd_max_sht45"] = self.calculate_vpd(thermal_max, sht45_humidity)
            vpd_results["enhanced_vpd_max_hdc3022"] = self.calculate_vpd(thermal_max, hdc3022_humidity)
            vpd_results["enhanced_vpd_max_avg"] = self.calculate_vpd(thermal_max, air_humidity)
            
            vpd_results["enhanced_vpd_avg_sht45"] = self.calculate_vpd(thermal_avg, sht45_humidity)
            vpd_results["enhanced_vpd_avg_hdc3022"] = self.calculate_vpd(thermal_avg, hdc3022_humidity)
            vpd_results["enhanced_vpd_avg_avg"] = self.calculate_vpd(thermal_avg, air_humidity)
            
            vpd_results["enhanced_vpd_modal_sht45"] = self.calculate_vpd(thermal_modal, sht45_humidity)
            vpd_results["enhanced_vpd_modal_hdc3022"] = self.calculate_vpd(thermal_modal, hdc3022_humidity)
            vpd_results["enhanced_vpd_modal_avg"] = self.calculate_vpd(thermal_modal, air_humidity)
            
            # Thermal VPD (pure thermal calculation)
            if thermal_avg is not None and air_humidity is not None:
                thermal_svp = self.calculate_svp(thermal_avg)
                thermal_avp = thermal_svp * (air_humidity / 100.0)
                vpd_results["thermal_vpd"] = round(thermal_svp - thermal_avp, 3)
            
            # Main Enhanced VPD (average of air + canopy VPD)
            air_vpd = vpd_results.get("air_vpd")
            canopy_vpd = vpd_results.get("canopy_vpd_avg")
            if air_vpd is not None and canopy_vpd is not None:
                vpd_results["enhanced_vpd"] = round((air_vpd + canopy_vpd) / 2, 3)
            
            logging.info(f"🧮 VPD calculations complete - Air: {air_vpd:.2f} kPa, Enhanced: {vpd_results.get('enhanced_vpd', 0):.2f} kPa")
            return vpd_results
            
        except Exception as e:
            logging.error(f"❌ VPD calculation error: {e}")
            return {}
    
    def get_vpd_interpretation(self, vpd_value: float) -> Dict[str, str]:
        """Get VPD interpretation and recommendations"""
        if vpd_value is None:
            return {"status": "unknown", "message": "VPD data unavailable", "color": "#888"}
        
        if vpd_value < 0.4:
            return {
                "status": "too_low",
                "message": "VPD too low - Risk of fungal diseases",
                "recommendation": "Increase temperature or decrease humidity",
                "color": "#2196f3"
            }
        elif vpd_value <= 0.8:
            return {
                "status": "low",
                "message": "VPD low - Slow transpiration",
                "recommendation": "Consider slight temperature increase",
                "color": "#4caf50"
            }
        elif vpd_value <= 1.2:
            return {
                "status": "optimal",
                "message": "VPD optimal - Good growing conditions",
                "recommendation": "Maintain current conditions",
                "color": "#8bc34a"
            }
        elif vpd_value <= 1.6:
            return {
                "status": "high",
                "message": "VPD high - Increased transpiration",
                "recommendation": "Monitor plant stress, consider humidity increase",
                "color": "#ff9800"
            }
        else:
            return {
                "status": "too_high",
                "message": "VPD too high - Risk of plant stress",
                "recommendation": "Increase humidity or decrease temperature",
                "color": "#f44336"
            }
