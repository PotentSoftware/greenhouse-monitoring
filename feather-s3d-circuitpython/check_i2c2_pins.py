"""
Check I2C2 pin configuration on Feather S3[D]
"""

import board
import busio

print("🔍 I2C2 Pin Discovery")
print("=" * 30)

print(f"📋 Board ID: {board.board_id}")

# Check I2C2 function
print("\n🔧 Investigating I2C2 function...")
try:
    i2c2_func = board.I2C2
    print(f"✅ I2C2 function exists: {i2c2_func}")
    print(f"   Type: {type(i2c2_func)}")
    
    # Try to get help/info about I2C2
    try:
        print(f"   Help: {help(i2c2_func)}")
    except:
        pass
        
except Exception as e:
    print(f"❌ I2C2 function error: {e}")

# Create I2C2 instance and inspect
print("\n🔧 Creating I2C2 instance...")
try:
    i2c2 = board.I2C2()
    print(f"✅ I2C2 instance created: {i2c2}")
    print(f"   Type: {type(i2c2)}")
    
    # Try to get pin info
    try:
        print(f"   SCL pin: {i2c2.scl_pin if hasattr(i2c2, 'scl_pin') else 'Unknown'}")
        print(f"   SDA pin: {i2c2.sda_pin if hasattr(i2c2, 'sda_pin') else 'Unknown'}")
    except Exception as e:
        print(f"   Pin info error: {e}")
    
    # Scan for devices
    print("\n🔍 Scanning I2C2 for devices...")
    while not i2c2.try_lock():
        pass
    
    devices = i2c2.scan()
    i2c2.unlock()
    
    if devices:
        print(f"✅ Found {len(devices)} device(s) on I2C2:")
        for device in devices:
            print(f"   - 0x{device:02x}")
    else:
        print("❌ No devices found on I2C2")
    
    i2c2.deinit()
    
except Exception as e:
    print(f"❌ I2C2 instance error: {e}")

# Check for alternative I2C2 pins
print("\n🔍 Looking for I2C2-related pins...")
pin_list = [attr for attr in dir(board) if not attr.startswith('_')]
i2c2_pins = [pin for pin in pin_list if '2' in pin and any(keyword in pin.upper() for keyword in ['SCL', 'SDA', 'I2C'])]

if i2c2_pins:
    print("🎯 Potential I2C2 pins found:")
    for pin in i2c2_pins:
        try:
            pin_obj = getattr(board, pin)
            print(f"   {pin:15s} = {pin_obj}")
        except Exception as e:
            print(f"   {pin:15s} = ERROR: {e}")
else:
    print("❌ No obvious I2C2 pins found")

# Check STEMMA QT connector pins
print("\n🔍 Checking for STEMMA QT specific pins...")
stemma_keywords = ['STEMMA', 'QT', 'QWIIC', 'CONNECTOR']
stemma_pins = []
for pin in pin_list:
    if any(keyword in pin.upper() for keyword in stemma_keywords):
        stemma_pins.append(pin)

if stemma_pins:
    print("🎯 STEMMA QT related pins:")
    for pin in stemma_pins:
        try:
            pin_obj = getattr(board, pin)
            print(f"   {pin:15s} = {pin_obj}")
        except Exception as e:
            print(f"   {pin:15s} = ERROR: {e}")
else:
    print("❌ No STEMMA QT specific pins found")

print("\n✅ I2C2 investigation complete!")
print("🔄 Analysis will help determine sensor connections")
