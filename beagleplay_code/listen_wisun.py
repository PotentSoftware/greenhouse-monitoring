#!/usr/bin/env python3

import socket
import time
import json
import logging
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def listen_for_data(interface="lowpan0", port=5678):
    """Listen for data from BeagleConnect Freedom over Wi-SUN"""
    try:
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to the interface and port
        try:
            interface_index = socket.if_nametoindex(interface)
        except OSError:
            logger.error(f"Interface {interface} not found")
            raise
        sock.bind(("::", port, 0, interface_index))
        
        logger.info(f"Listening for data on {interface}::{port}")
        
        while True:
            # Receive data
            data, addr = sock.recvfrom(1024)
            logger.info(f"Received {len(data)} bytes from {addr}")
            
            try:
                # Try to parse as JSON
                json_data = json.loads(data.decode('utf-8'))
                logger.info(f"Parsed JSON data: {json_data}")
            except json.JSONDecodeError:
                # Not JSON, try to parse as binary data
                logger.info(f"Raw data (hex): {data.hex()}")
                
                # Try to interpret as temperature data (assuming float values)
                if len(data) % 4 == 0:
                    float_count = len(data) // 4
                    float_values = struct.unpack(f"<{float_count}f", data)
                    logger.info(f"Interpreted as {float_count} float values: {float_values}")
            
    except Exception as e:
        logger.error(f"Error listening for data: {e}")
    finally:
        sock.close()

def main():
    try:
        # Check if lowpan0 interface exists
        import subprocess
        result = subprocess.run(["ifconfig", "lowpan0"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("lowpan0 interface not found. Is Wi-SUN configured?")
            return
        
        # Start listening
        listen_for_data()
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
