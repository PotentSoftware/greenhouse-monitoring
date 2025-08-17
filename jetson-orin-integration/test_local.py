#!/usr/bin/env python3
"""
Local Testing Script for Jetson Orin Nano Integration
Tests all components locally before deployment
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_imports():
    """Test all module imports"""
    print("🧪 Testing module imports...")
    
    try:
        import jetson_config as config
        print("✅ Config module imported")
        
        from sensor_manager import SensorManager
        print("✅ SensorManager imported")
        
        from vpd_calculator import VPDCalculator
        print("✅ VPDCalculator imported")
        
        from thermal_processor import ThermalProcessor
        print("✅ ThermalProcessor imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n🔧 Testing configuration...")
    
    try:
        import jetson_config as config
        
        print(f"Jetson IP: {config.JETSON_IP}")
        print(f"Jetson Port: {config.JETSON_PORT}")
        print(f"Feather S3[D] IPs: {config.FEATHER_S3D_IPS}")
        print(f"tCam Host: {config.TCAM_HOST}:{config.TCAM_PORT}")
        print(f"Data Directory: {config.DATA_DIR}")
        
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_sensor_manager():
    """Test sensor manager initialization and basic functionality"""
    print("\n📡 Testing SensorManager...")
    
    try:
        import jetson_config as config
        from sensor_manager import SensorManager
        
        # Initialize sensor manager
        sensor_manager = SensorManager(config)
        print("✅ SensorManager initialized")
        
        # Test data structure
        data = sensor_manager.get_sensor_data()
        print("✅ Sensor data structure created")
        
        # Print structure
        print("Sensor data keys:", list(data.keys()))
        print("Feather S3[D] keys:", list(data["feather_s3d"].keys()))
        print("Thermal camera keys:", list(data["thermal_camera"].keys()))
        
        return True
    except Exception as e:
        print(f"❌ SensorManager error: {e}")
        return False

def test_vpd_calculator():
    """Test VPD calculator"""
    print("\n🧮 Testing VPDCalculator...")
    
    try:
        from vpd_calculator import VPDCalculator
        
        vpd_calc = VPDCalculator()
        print("✅ VPDCalculator initialized")
        
        # Test basic VPD calculation
        vpd = vpd_calc.calculate_vpd(25.0, 60.0)  # 25°C, 60% RH
        print(f"✅ Basic VPD calculation: {vpd:.3f} kPa")
        
        # Test SVP calculation
        svp = vpd_calc.calculate_svp(25.0)
        print(f"✅ SVP calculation: {svp:.3f} kPa")
        
        # Test VPD interpretation
        interpretation = vpd_calc.get_vpd_interpretation(vpd)
        print(f"✅ VPD interpretation: {interpretation['status']} - {interpretation['message']}")
        
        return True
    except Exception as e:
        print(f"❌ VPDCalculator error: {e}")
        return False

def test_thermal_processor():
    """Test thermal processor"""
    print("\n🖼️ Testing ThermalProcessor...")
    
    try:
        import jetson_config as config
        from thermal_processor import ThermalProcessor
        import numpy as np
        
        thermal_proc = ThermalProcessor(config)
        print("✅ ThermalProcessor initialized")
        
        # Test with simulated thermal data
        thermal_image = np.random.uniform(20, 30, (120, 160))  # Simulate thermal image
        print("✅ Simulated thermal image created")
        
        # Test processing
        results = thermal_proc.process_thermal_image(thermal_image)
        print(f"✅ Thermal processing complete: {results.get('processing_method', 'unknown')}")
        
        # Test canopy temperature
        canopy_temp = thermal_proc.get_canopy_temperature(thermal_image)
        print(f"✅ Canopy temperature: {canopy_temp:.1f}°C")
        
        # Test available strategies
        strategies = thermal_proc.get_available_strategies()
        print(f"✅ Available strategies: {list(strategies.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ ThermalProcessor error: {e}")
        return False

def test_integration():
    """Test full integration"""
    print("\n🔗 Testing full integration...")
    
    try:
        import jetson_config as config
        from sensor_manager import SensorManager
        from vpd_calculator import VPDCalculator
        from thermal_processor import ThermalProcessor
        import numpy as np
        
        # Initialize all components
        sensor_manager = SensorManager(config)
        vpd_calc = VPDCalculator()
        thermal_proc = ThermalProcessor(config)
        print("✅ All components initialized")
        
        # Simulate sensor data
        sensor_data = sensor_manager.get_sensor_data()
        sensor_data["feather_s3d"]["sht45"] = {"temperature": 22.5, "humidity": 65.0}
        sensor_data["feather_s3d"]["hdc3022"] = {"temperature": 23.0, "humidity": 63.0}
        sensor_data["feather_s3d"]["averages"] = {"temperature": 22.75, "humidity": 64.0}
        
        # Simulate thermal data
        thermal_image = np.random.uniform(20, 30, (120, 160))
        thermal_results = thermal_proc.process_thermal_image(thermal_image)
        sensor_data["thermal_camera"]["min_temp"] = thermal_results.get("min_temp", 20.0)
        sensor_data["thermal_camera"]["max_temp"] = thermal_results.get("max_temp", 30.0)
        sensor_data["thermal_camera"]["avg_temp"] = thermal_results.get("mean_temp", 25.0)
        sensor_data["thermal_camera"]["modal_temp"] = thermal_results.get("mode_temp", 25.0)
        
        print("✅ Simulated sensor data created")
        
        # Test VPD calculations
        vpd_results = vpd_calc.calculate_all_vpd_types(sensor_data)
        print(f"✅ VPD calculations complete: {len(vpd_results)} VPD types calculated")
        
        # Print some results
        print(f"Air VPD: {vpd_results.get('air_vpd', 0):.3f} kPa")
        print(f"Enhanced VPD: {vpd_results.get('enhanced_vpd', 0):.3f} kPa")
        print(f"Canopy VPD (avg): {vpd_results.get('canopy_vpd_avg', 0):.3f} kPa")
        
        return True
    except Exception as e:
        print(f"❌ Integration error: {e}")
        return False

def test_network_connectivity():
    """Test network connectivity to sensors"""
    print("\n🌐 Testing network connectivity...")
    
    try:
        import requests
        import socket
        
        # Test Feather S3[D] connectivity
        try:
            response = requests.get("http://192.168.1.81:8080/sensors", timeout=5)
            if response.status_code == 200:
                print("✅ Feather S3[D] reachable")
            else:
                print(f"⚠️ Feather S3[D] returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Feather S3[D] not reachable: {e}")
        
        # Test tCam-Mini connectivity
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('192.168.1.130', 5001))
            sock.close()
            if result == 0:
                print("✅ tCam-Mini reachable")
            else:
                print("❌ tCam-Mini not reachable")
        except Exception as e:
            print(f"❌ tCam-Mini connection error: {e}")
        
        # Test BeaglePlay (for comparison)
        try:
            response = requests.get("http://192.168.1.203:8080/", timeout=5)
            if response.status_code == 200:
                print("✅ BeaglePlay reachable")
            else:
                print(f"⚠️ BeaglePlay returned status {response.status_code}")
        except Exception as e:
            print(f"❌ BeaglePlay not reachable: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Network test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 Jetson Orin Nano Integration - Local Testing")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("SensorManager", test_sensor_manager),
        ("VPDCalculator", test_vpd_calculator),
        ("ThermalProcessor", test_thermal_processor),
        ("Full Integration", test_integration),
        ("Network Connectivity", test_network_connectivity)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🧪 Test Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())
