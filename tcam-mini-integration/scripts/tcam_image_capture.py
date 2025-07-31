#!/usr/bin/env python3
"""
tCam-Mini Image Capture and Analysis Script

This script captures thermal images from tCam-Mini and performs basic analysis
to understand the data format and prepare for computer vision development.
"""

import requests
import json
import numpy as np
import cv2
import time
import os
from datetime import datetime
import matplotlib.pyplot as plt

class TCamCapture:
    def __init__(self, ip_address, save_directory="test_images"):
        self.ip = ip_address
        self.save_dir = save_directory
        self.base_url = f"http://{ip_address}"
        
        # Create save directory
        os.makedirs(save_directory, exist_ok=True)
        
        print(f"🔧 TCam-Mini Capture initialized for {ip_address}")
    
    def test_connection(self):
        """Test connection to tCam-Mini"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            print(f"✅ Connection successful to {self.ip}")
            return True
        except Exception as e:
            print(f"❌ Connection failed to {self.ip}: {e}")
            return False
    
    def get_camera_status(self):
        """Get camera status and configuration"""
        endpoints = ['/status', '/camera', '/config', '/api/status']
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"📊 Camera status from {endpoint}:")
                        print(json.dumps(data, indent=2))
                        return data
                    except:
                        print(f"📊 Camera status from {endpoint}: {response.text[:200]}...")
                        return response.text
            except Exception as e:
                continue
        
        print("⚠️ Could not get camera status")
        return None
    
    def capture_thermal_image(self, save_image=True):
        """Capture thermal image with temperature data"""
        timestamp = datetime.now().isoformat()
        
        # Try different image endpoints
        image_endpoints = [
            '/image',
            '/api/image', 
            '/thermal_data',
            '/stream',
            '/capture'
        ]
        
        for endpoint in image_endpoints:
            try:
                print(f"🔍 Trying image capture from {endpoint}...")
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'json' in content_type:
                        # JSON response with temperature data
                        data = response.json()
                        print(f"✅ Got JSON thermal data from {endpoint}")
                        
                        if save_image:
                            filename = f"thermal_data_{timestamp.replace(':', '-')}.json"
                            filepath = os.path.join(self.save_dir, filename)
                            with open(filepath, 'w') as f:
                                json.dump(data, f, indent=2)
                            print(f"💾 Saved thermal data to {filepath}")
                        
                        return self.process_thermal_data(data, timestamp)
                    
                    elif 'image' in content_type:
                        # Image response
                        print(f"✅ Got image data from {endpoint}")
                        
                        if save_image:
                            filename = f"thermal_image_{timestamp.replace(':', '-')}.jpg"
                            filepath = os.path.join(self.save_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            print(f"💾 Saved image to {filepath}")
                        
                        return self.process_image_data(response.content, timestamp)
                    
                    else:
                        print(f"📄 Unknown content type: {content_type}")
                        print(f"📄 Content preview: {response.content[:100]}...")
                
            except Exception as e:
                print(f"❌ Error with {endpoint}: {e}")
                continue
        
        print("❌ Could not capture thermal image from any endpoint")
        return None
    
    def process_thermal_data(self, data, timestamp):
        """Process JSON thermal data"""
        print("🔬 Analyzing thermal data structure...")
        
        # Look for temperature arrays or pixel data
        temp_data = None
        image_data = None
        
        # Common field names to check
        temp_fields = ['pixels', 'temperature_array', 'thermal_data', 'temps', 'data']
        image_fields = ['image', 'thermal_image', 'bitmap', 'frame']
        
        for field in temp_fields:
            if field in data:
                temp_data = data[field]
                print(f"📊 Found temperature data in field: {field}")
                break
        
        for field in image_fields:
            if field in data:
                image_data = data[field]
                print(f"🖼️ Found image data in field: {field}")
                break
        
        if temp_data:
            self.analyze_temperature_array(temp_data, timestamp)
        
        if image_data:
            self.analyze_image_array(image_data, timestamp)
        
        # Print full data structure for analysis
        print("📋 Full data structure:")
        print(json.dumps(data, indent=2)[:1000] + "..." if len(str(data)) > 1000 else json.dumps(data, indent=2))
        
        return data
    
    def process_image_data(self, image_bytes, timestamp):
        """Process binary image data"""
        print("🖼️ Processing binary image data...")
        
        try:
            # Try to decode as image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None:
                print(f"✅ Decoded image: {img.shape}")
                
                # Save processed image
                filename = f"processed_image_{timestamp.replace(':', '-')}.png"
                filepath = os.path.join(self.save_dir, filename)
                cv2.imwrite(filepath, img)
                print(f"💾 Saved processed image to {filepath}")
                
                return img
            else:
                print("❌ Could not decode image data")
                return None
                
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            return None
    
    def analyze_temperature_array(self, temp_data, timestamp):
        """Analyze temperature array data"""
        try:
            if isinstance(temp_data, list):
                temps = np.array(temp_data)
            else:
                temps = np.array(temp_data)
            
            print(f"🌡️ Temperature array analysis:")
            print(f"   Shape: {temps.shape}")
            print(f"   Min temp: {np.min(temps):.2f}°C")
            print(f"   Max temp: {np.max(temps):.2f}°C")
            print(f"   Mean temp: {np.mean(temps):.2f}°C")
            print(f"   Std dev: {np.std(temps):.2f}°C")
            
            # Create thermal image visualization
            if len(temps.shape) == 1:
                # Assume 160x120 for tCam-Mini
                if len(temps) == 19200:  # 160*120
                    thermal_image = temps.reshape(120, 160)
                elif len(temps) == 768:  # 32*24 (old camera)
                    thermal_image = temps.reshape(24, 32)
                else:
                    print(f"⚠️ Unexpected array size: {len(temps)}")
                    return
            else:
                thermal_image = temps
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.imshow(thermal_image, cmap='hot', interpolation='nearest')
            plt.colorbar(label='Temperature (°C)')
            plt.title('Thermal Image')
            
            plt.subplot(2, 2, 2)
            plt.hist(temps.flatten(), bins=50, alpha=0.7)
            plt.xlabel('Temperature (°C)')
            plt.ylabel('Pixel Count')
            plt.title('Temperature Distribution')
            
            plt.subplot(2, 2, 3)
            plt.plot(temps.flatten())
            plt.xlabel('Pixel Index')
            plt.ylabel('Temperature (°C)')
            plt.title('Temperature Profile')
            
            plt.subplot(2, 2, 4)
            # Create false color image
            normalized = cv2.normalize(thermal_image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
            plt.imshow(cv2.cvtColor(colored, cv2.COLOR_BGR2RGB))
            plt.title('False Color Thermal')
            
            plt.tight_layout()
            
            # Save visualization
            filename = f"thermal_analysis_{timestamp.replace(':', '-')}.png"
            filepath = os.path.join(self.save_dir, filename)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.show()
            print(f"📊 Saved thermal analysis to {filepath}")
            
        except Exception as e:
            print(f"❌ Error analyzing temperature data: {e}")
    
    def analyze_image_array(self, image_data, timestamp):
        """Analyze image array data"""
        try:
            if isinstance(image_data, list):
                img_array = np.array(image_data)
            else:
                img_array = image_data
            
            print(f"🖼️ Image array analysis:")
            print(f"   Shape: {img_array.shape}")
            print(f"   Data type: {img_array.dtype}")
            print(f"   Min value: {np.min(img_array)}")
            print(f"   Max value: {np.max(img_array)}")
            
        except Exception as e:
            print(f"❌ Error analyzing image data: {e}")

def main():
    """Main capture function"""
    print("📸 tCam-Mini Image Capture and Analysis")
    print("=======================================")
    
    # Test multiple potential IP addresses
    test_ips = ['192.168.1.100', '192.168.1.101', '192.168.1.176', '192.168.1.200']
    
    tcam = None
    for ip in test_ips:
        test_tcam = TCamCapture(ip)
        if test_tcam.test_connection():
            tcam = test_tcam
            break
    
    if not tcam:
        print("❌ No tCam-Mini found. Please check:")
        print("1. WiFi configuration")
        print("2. IP address")
        print("3. Network connectivity")
        return
    
    # Get camera status
    tcam.get_camera_status()
    
    # Capture and analyze thermal image
    print("\n📸 Capturing thermal image...")
    result = tcam.capture_thermal_image(save_image=True)
    
    if result:
        print("✅ Image capture and analysis complete!")
        print(f"📁 Check the '{tcam.save_dir}' directory for saved files")
    else:
        print("❌ Image capture failed")

if __name__ == "__main__":
    main()