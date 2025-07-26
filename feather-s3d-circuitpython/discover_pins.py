"""
Discover available pins on Feather S3[D]
"""

import board
import time

print("🌱 Feather S3[D] Pin Discovery")
print("=" * 40)

print(f"📋 Board ID: {board.board_id}")

print("\n📍 All available pins:")
pin_list = [attr for attr in dir(board) if not attr.startswith('_')]
pin_list.sort()

for i, pin in enumerate(pin_list):
    try:
        pin_obj = getattr(board, pin)
        print(f"  {i+1:2d}. {pin:15s} = {pin_obj}")
    except Exception as e:
        print(f"  {i+1:2d}. {pin:15s} = ERROR: {e}")

print("\n🔍 Looking for I2C-related pins:")
i2c_pins = [pin for pin in pin_list if any(keyword in pin.upper() for keyword in ['SCL', 'SDA', 'I2C'])]
if i2c_pins:
    for pin in i2c_pins:
        try:
            pin_obj = getattr(board, pin)
            print(f"  ✅ {pin:15s} = {pin_obj}")
        except Exception as e:
            print(f"  ❌ {pin:15s} = ERROR: {e}")
else:
    print("  ❌ No obvious I2C pins found")

print("\n🔍 Looking for STEMMA QT pins:")
stemma_pins = [pin for pin in pin_list if any(keyword in pin.upper() for keyword in ['STEMMA', 'QT', 'QWIIC'])]
if stemma_pins:
    for pin in stemma_pins:
        try:
            pin_obj = getattr(board, pin)
            print(f"  ✅ {pin:15s} = {pin_obj}")
        except Exception as e:
            print(f"  ❌ {pin:15s} = ERROR: {e}")
else:
    print("  ❌ No STEMMA QT pins found")

print("\n🔍 Testing basic I2C creation:")
try:
    import busio
    # Try default I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    print("  ✅ Default I2C created successfully")
    i2c.deinit()
except Exception as e:
    print(f"  ❌ Default I2C failed: {e}")

print("\n✅ Pin discovery complete!")
print("Press Ctrl+C to stop")
