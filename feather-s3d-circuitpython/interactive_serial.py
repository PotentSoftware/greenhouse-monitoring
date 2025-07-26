#!/usr/bin/env python3
"""
Interactive serial tool for Feather S3[D] - can send commands
"""

import serial
import time
import sys

def interactive_serial():
    try:
        print("🔌 Connecting to Feather S3[D]...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
        print("✅ Connected! Sending test commands...")
        print("-" * 50)
        
        # Send Ctrl+D to reload/restart
        print("📤 Sending Ctrl+D to restart...")
        ser.write(b'\x04')  # Ctrl+D
        time.sleep(2)
        
        # Read any output
        output_lines = []
        start_time = time.time()
        while time.time() - start_time < 10:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8', errors='ignore').strip()
                if data:
                    output_lines.append(data)
                    print(f"📥 {data}")
            time.sleep(0.1)
        
        print(f"\n📊 Captured {len(output_lines)} lines of output")
        
        if not output_lines or all('>>>' in line for line in output_lines):
            print("🔄 Still in REPL mode, trying to run code manually...")
            
            # Try to import and run our test
            commands = [
                "import board",
                "print('Board test from REPL')",
                "print(f'Board ID: {board.board_id}')",
                "import busio",
                "print('Busio imported successfully')"
            ]
            
            for cmd in commands:
                print(f"📤 Sending: {cmd}")
                ser.write(f"{cmd}\r\n".encode())
                time.sleep(1)
                
                # Read response
                response_start = time.time()
                while time.time() - response_start < 2:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8', errors='ignore').strip()
                        if data and data != '>>>':
                            print(f"📥 {data}")
                    time.sleep(0.1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()
            print("🔌 Serial connection closed")

if __name__ == "__main__":
    interactive_serial()
