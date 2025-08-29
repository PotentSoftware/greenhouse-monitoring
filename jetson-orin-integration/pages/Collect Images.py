#!/usr/bin/env python3
import os
import json
import base64
import socket
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import streamlit as st

st.set_page_config(page_title="Collect Thermal Images", page_icon="📷", layout="wide")

CAMERA_HOST = "192.168.1.130"
CAMERA_PORT = 5001
IMG_SHAPE = (120, 160)
KELVIN_OFFSET = 273.15
THERMAL_RES = 0.01

@st.cache_data(show_spinner=False)
def desktop_path() -> Path:
    p = Path.home() / "Desktop"
    p.mkdir(exist_ok=True)
    return p

def test_thermal_camera_connection():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect((CAMERA_HOST, CAMERA_PORT))
        command = json.dumps({"cmd": "get_image"}) + "\n"
        stx_command = b"\x02" + command.encode() + b"\x03"
        sock.sendall(stx_command)
        data = sock.recv(64)
        sock.close()
        if not data:
            return False, "No response from camera"
        if b"\x02" not in data:
            return False, "Response missing STX"
        return True, "TCP connected and response received"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def capture_single_thermal_image():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((CAMERA_HOST, CAMERA_PORT))
        command = json.dumps({"cmd": "get_image"}) + "\n"
        stx_command = b"\x02" + command.encode() + b"\x03"
        sock.sendall(stx_command)

        buffer = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk
            if b"\x03" in chunk:
                break
        sock.close()

        if buffer:
            start = buffer.find(b"\x02")
            end = buffer.rfind(b"\x03")
            if start == -1 or end == -1 or end <= start:
                st.error("Malformed response framing from camera (missing STX/ETX)")
                return None
            payload = buffer[start+1:end]
            try:
                thermal_data = json.loads(payload.decode(errors='ignore'))
            except Exception as je:
                st.error(f"JSON decode error from camera: {je}")
                return None

            if 'radiometric' in thermal_data:
                img_b64 = thermal_data['radiometric']
                try:
                    img_data = base64.b64decode(img_b64)
                except Exception as de:
                    st.error(f"Base64 decode error: {de}\nRadiometric (truncated): {str(img_b64)[:80]}...")
                    return None
                thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                thermal_raw = thermal_array.reshape(IMG_SHAPE)
                thermal_celsius = (thermal_raw * THERMAL_RES) - KELVIN_OFFSET
                return thermal_celsius
            else:
                st.error("Camera response missing 'radiometric' field")
        return None
    except Exception as e:
        st.error(f"❌ Error capturing thermal image: {e}")
        return None


def main():
    st.title("📷 Collect Thermal Images")
    st.info("Images are saved as .npy arrays under ~/Desktop/thermal_collection_[timestamp]/")

    with st.expander("Camera", expanded=True):
        col_t1, col_t2 = st.columns([1,3])
        if col_t1.button("🔌 Test Camera Connectivity"):
            ok, msg = test_thermal_camera_connection()
            if ok:
                st.success(f"Camera OK: {msg}")
            else:
                st.error(f"Camera problem: {msg}")
        st.code(f"Host: {CAMERA_HOST}, Port: {CAMERA_PORT}")

    col1, col2, col3 = st.columns(3)
    with col1:
        num_images = st.number_input("Number of Images", min_value=1, max_value=50, value=10)
    with col2:
        interval_seconds = st.number_input("Interval (seconds)", min_value=1, max_value=5, value=3)
    with col3:
        st.write("")
        st.write("")
        start_btn = st.button("Start Collection", type="primary")

    if start_btn:
        # Pre-check
        ok, msg = test_thermal_camera_connection()
        if not ok:
            st.error(f"Cannot start collection: {msg}")
            st.stop()

        dpath = desktop_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        collection_dir = dpath / f"thermal_collection_{timestamp}"
        collection_dir.mkdir(exist_ok=True)
        st.success(f"📁 Created collection directory: {collection_dir}")

        metadata = {
            "collection_start": datetime.now().isoformat(),
            "num_images_requested": int(num_images),
            "interval_seconds": int(interval_seconds),
            "collection_directory": str(collection_dir),
            "images_captured": [],
            "capture_errors": [],
            "thermal_camera_config": {
                "host": CAMERA_HOST,
                "port": CAMERA_PORT,
                "resolution": "160x120",
                "thermal_resolution": THERMAL_RES,
                "kelvin_offset": KELVIN_OFFSET
            }
        }

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(int(num_images)):
            progress_bar.progress((i + 1) / int(num_images))
            status_text.text(f"📸 Capturing image {i+1}/{int(num_images)}...")

            arr = capture_single_thermal_image()
            if arr is None:
                err = f"Failed to capture image {i+1}"
                st.error(f"❌ {err}")
                metadata["capture_errors"].append({
                    "sequence_number": i + 1,
                    "error": err,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                img_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"thermal_image_{i+1:02d}_{img_timestamp}.npy"
                filepath = collection_dir / filename
                try:
                    np.save(filepath, arr)
                    stats = {
                        "min_temp": float(np.nanmin(arr)),
                        "max_temp": float(np.nanmax(arr)),
                        "avg_temp": float(np.nanmean(arr)),
                        "median_temp": float(np.nanmedian(arr)),
                        "total_pixels": int(arr.size)
                    }
                    metadata["images_captured"].append({
                        "filename": filename,
                        "capture_time": datetime.now().isoformat(),
                        "sequence_number": i + 1,
                        "image_shape": list(arr.shape),
                        **stats
                    })
                    st.success(f"✅ Saved {filename} - Temp range: {stats['min_temp']:.1f}°C to {stats['max_temp']:.1f}°C")
                except Exception as e:
                    err = f"Failed to save image {i+1}: {e}"
                    st.error(f"❌ {err}")
                    metadata["capture_errors"].append({
                        "sequence_number": i + 1,
                        "error": err,
                        "timestamp": datetime.now().isoformat()
                    })

            if i < int(num_images) - 1:
                status_text.text(f"⏱️ Waiting {int(interval_seconds)} seconds for next capture...")
                time.sleep(int(interval_seconds))

        metadata["collection_end"] = datetime.now().isoformat()
        metadata["images_successfully_captured"] = len(metadata["images_captured"])
        metadata["total_errors"] = len(metadata["capture_errors"])

        try:
            with open(collection_dir / "collection_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            with open(collection_dir / "README.txt", 'w') as f:
                f.write("Thermal Image Collection Summary\n")
                f.write("================================\n\n")
                f.write(f"Collection Date: {metadata['collection_start']}\n")
                f.write(f"Images Requested: {metadata['num_images_requested']}\n")
                f.write(f"Images Captured: {metadata['images_successfully_captured']}\n")
                f.write(f"Capture Interval: {metadata['interval_seconds']} seconds\n")
                f.write(f"Total Errors: {metadata['total_errors']}\n\n")
        except Exception as e:
            st.error(f"❌ Failed to write metadata: {e}")

        progress_bar.progress(1.0)
        status_text.text("🎉 Collection complete!")
        st.balloons()

if __name__ == "__main__":
    main()
