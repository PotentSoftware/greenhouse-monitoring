#!/usr/bin/env python3
"""
Improved serial port reader for Feather S3[D]
"""

import serial
import time
import sys

def read_feather_serial():
    try:
        # Open serial connection with different settings
        print("🔌 Attempting to connect to Feather S3[D]...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
        print("✅ Connected to Feather S3[D] on /dev/ttyACM0")
        print("📡 Reading serial output (Ctrl+C to stop)...")
        print("-" * 50)
        
        # Send a newline to potentially trigger output
        ser.write(b'\r\n')
        time.sleep(0.5)
        
        # Clear any existing data
        ser.flushInput()
        
        # Read for 60 seconds or until Ctrl+C
        start_time = time.time()
        line_count = 0
        while time.time() - start_time < 60:
            try:
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        line_count += 1
                        print(f"[{line_count:03d}] {data}")
                else:
                    # Send periodic newlines to check if board is responsive
                    if int(time.time() - start_time) % 10 == 0:
                        ser.write(b'\r\n')
                        time.sleep(0.1)
                time.sleep(0.05)
            except Exception as e:
                print(f"⚠️  Read error: {e}")
                time.sleep(0.5)
                    
    except serial.SerialException as e:
        print(f"❌ Serial connection failed: {e}")
        print("💡 Try: sudo chmod 666 /dev/ttyACM0")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'ser' in locals():
            ser.close()
            print("🔌 Serial connection closed")
    
    return True

if __name__ == "__main__":
    read_feather_serial()
