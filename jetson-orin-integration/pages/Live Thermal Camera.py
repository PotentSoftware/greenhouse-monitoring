import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import socket
import json
import matplotlib.pyplot as plt
from scipy import stats
import requests
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Live Thermal Camera",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ Live Thermal Camera Feed")

# Thermal camera configuration
TCAM_HOST = "192.168.1.130"
TCAM_PORT = 5001
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 120

def get_thermal_image():
    """Get thermal image from Jetson's local thermal camera service"""
    try:
        # Try direct tCam-Mini socket connection (primary source after power cycle)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect(("192.168.1.130", 5001))
            
            # Send get_image command with proper delimiters
            command = {"cmd": "get_image"}
            json_cmd = json.dumps(command)
            cmd_with_delimiters = b'\x02' + json_cmd.encode() + b'\x03'
            sock.send(cmd_with_delimiters)
            
            # Receive response
            response = b''
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response += chunk
                if b'\x03' in chunk:
                    break
            
            sock.close()
            
            # Parse response
            if response.startswith(b'\x02') and b'\x03' in response:
                etx_pos = response.find(b'\x03')
                json_response = response[1:etx_pos].decode()
                data = json.loads(json_response)
                
                if 'radiometric' in data:
                    import base64
                    img_data = base64.b64decode(data['radiometric'])
                    thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                    thermal_raw = thermal_array.reshape((120, 160))
                    
                    # Convert Kelvin*100 to Celsius
                    thermal_celsius = (thermal_raw.astype(float) * 0.01) - 273.15
                    return thermal_celsius, True
        except Exception as e:
            print(f"Failed to connect directly to tCam-Mini: {e}")
        
        # Try tcam_proxy_server on Jetson (fallback - simulated data)
        try:
            response = requests.get("http://localhost:5002/thermal_data", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'thermal_data' in data:
                    thermal_array = np.array(data['thermal_data'])
                    if thermal_array.size == 19200:
                        thermal_array = thermal_array.reshape((120, 160))
                        return thermal_array, False  # Mark as simulated data
        except Exception as e:
            print(f"Failed to connect to tcam_proxy_server: {e}")
        
        # If all connections fail, return None to show error message
        return None
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None, False

def get_real_thermal_image():
    """Attempt to get real thermal image from tCam-Mini"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect(("192.168.1.130", 5001))
        
        # Send get_image command
        command = {"cmd": "get_image"}
        json_cmd = json.dumps(command)
        cmd_with_delimiters = b'\x02' + json_cmd.encode() + b'\x03'
        sock.send(cmd_with_delimiters)
        
        # Receive response
        response = b''
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            response += chunk
            if b'\x03' in chunk:
                break
        
        sock.close()
        
        # Parse response
        if response.startswith(b'\x02') and b'\x03' in response:
            etx_pos = response.find(b'\x03')
            json_response = response[1:etx_pos].decode()
            data = json.loads(json_response)
            
            if 'radiometric' in data:
                import base64
                img_data = base64.b64decode(data['radiometric'])
                thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                thermal_raw = thermal_array.reshape((120, 160))
                
                # Convert Kelvin*100 to Celsius
                thermal_celsius = (thermal_raw.astype(float) * 0.01) - 273.15
                return thermal_celsius
        
        return None
        
    except Exception:
        return None

def calculate_statistics(thermal_image):
    """Calculate thermal image statistics"""
    # Filter out negative values (faulty pixels)
    valid_pixels = thermal_image[thermal_image > 0]
    
    if len(valid_pixels) == 0:
        return {
            'mean': 0, 'median': 0, 'mode': 0, 'std': 0,
            'min': 0, 'max': 0, 'valid_pixels': 0, 'total_pixels': thermal_image.size
        }
    
    # Calculate statistics
    mean_temp = np.mean(valid_pixels)
    median_temp = np.median(valid_pixels)
    
    # Calculate mode (most frequent temperature rounded to 0.1°C)
    rounded_temps = np.round(valid_pixels, 1)
    mode_result = stats.mode(rounded_temps, keepdims=True)
    mode_temp = mode_result.mode[0] if len(mode_result.mode) > 0 else median_temp
    
    std_temp = np.std(valid_pixels)
    min_temp = np.min(valid_pixels)
    max_temp = np.max(valid_pixels)
    
    return {
        'mean': mean_temp,
        'median': median_temp,
        'mode': mode_temp,
        'std': std_temp,
        'min': min_temp,
        'max': max_temp,
        'valid_pixels': len(valid_pixels),
        'total_pixels': thermal_image.size
    }

# Connection status and information
with st.expander("ℹ️ Thermal Camera Connection Status", expanded=False):
    col1, col2 = st.columns([3, 1])
    with col1:
        # Check connection status
        tcam_status = "Unknown"
        try:
            # Test direct tCam-Mini connection first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(("192.168.1.130", 5001))
            sock.close()
            tcam_status = "Connected to tCam-Mini (Real Data)"
        except:
            try:
                resp = requests.get("http://localhost:5002/status", timeout=2)
                if resp.status_code == 200:
                    tcam_status = "Connected to tCam Proxy Server (Simulated Data)"
            except:
                tcam_status = "No thermal camera connection"
        
        if "Connected" in tcam_status:
            st.success(f"✅ {tcam_status}")
        else:
            st.warning(f"⚠️ {tcam_status}")
            
        st.info("""
        **Connection Details:**
        - Direct tCam-Mini: 192.168.1.130:5001 (primary - real thermal data)
        - tCam Proxy Server: localhost:5002/thermal_data (fallback - simulated data)
        - Auto-refresh: Every 5 seconds
        """)
    with col2:
        if st.button("🔄 Refresh", key="refresh_thermal"):
            st.rerun()

result = get_thermal_image()

if result is not None:
    thermal_data, is_real_data = result
    
    # Display current time and data source info
    current_time = datetime.now().strftime("%H:%M:%S")
    data_source = "Real Data" if is_real_data else "Simulated Data"
    st.markdown(f"**Thermal Image ({data_source}) - Last Updated:** {current_time}")

    # Calculate statistics
    stats_data = calculate_statistics(thermal_data)
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🌡️ Thermal Image")
        
        # Create thermal image plot
        fig = go.Figure(data=go.Heatmap(
            z=thermal_data,
            colorscale='thermal',
            showscale=True,
            colorbar=dict(title="Temperature (°C)")
        ))
        
        fig.update_layout(
            title=f"Thermal Image - Range: {stats_data['min']:.1f}°C to {stats_data['max']:.1f}°C",
            xaxis_title="Pixel X",
            yaxis_title="Pixel Y",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Statistics")
        
        # Display statistics
        st.metric("🌡️ Mean Temperature", f"{stats_data['mean']:.2f}°C")
        st.metric("📊 Median Temperature", f"{stats_data['median']:.2f}°C")
        st.metric("🎯 Mode Temperature", f"{stats_data['mode']:.2f}°C")
        st.metric("📈 Std Deviation", f"{stats_data['std']:.2f}°C")
        st.metric("🔽 Min Temperature", f"{stats_data['min']:.2f}°C")
        st.metric("🔼 Max Temperature", f"{stats_data['max']:.2f}°C")
        
        # Pixel information
        st.markdown("---")
        st.markdown("**Pixel Information:**")
        st.write(f"Valid Pixels: {stats_data['valid_pixels']}")
        st.write(f"Total Pixels: {stats_data['total_pixels']}")
        valid_percentage = (stats_data['valid_pixels'] / stats_data['total_pixels']) * 100
        st.write(f"Valid Percentage: {valid_percentage:.1f}%")
    
    # Histogram section
    st.subheader("📈 Temperature Histogram")
    
    # Filter valid pixels for histogram
    valid_pixels = thermal_data[thermal_data > 0].flatten()
    
    if len(valid_pixels) > 0:
        # Create histogram
        hist_fig = px.histogram(
            x=valid_pixels,
            nbins=50,
            title="Distribution of Pixel Temperatures",
            labels={'x': 'Temperature (°C)', 'y': 'Pixel Count'},
            template="plotly_dark"
        )
        
        # Add statistical lines
        hist_fig.add_vline(x=stats_data['mean'], line_dash="dash", line_color="red", 
                          annotation_text=f"Mean: {stats_data['mean']:.2f}°C")
        hist_fig.add_vline(x=stats_data['median'], line_dash="dash", line_color="green", 
                          annotation_text=f"Median: {stats_data['median']:.2f}°C")
        hist_fig.add_vline(x=stats_data['mode'], line_dash="dash", line_color="blue", 
                          annotation_text=f"Mode: {stats_data['mode']:.2f}°C")
        
        st.plotly_chart(hist_fig, use_container_width=True)
    else:
        st.error("No valid temperature data for histogram")

else:
    st.error("❌ Failed to get thermal image data")
    st.info("⚠️ Using placeholder data - tCam-Mini at 192.168.1.130:5001 unavailable")

# Add auto-refresh
if st.button("🔄 Auto-refresh (5s)", key="auto_refresh"):
    st.rerun()

# Add manual refresh timer
import time
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# Auto-refresh every 5 seconds
if time.time() - st.session_state.last_refresh > 5:
    st.session_state.last_refresh = time.time()
    st.rerun()
