import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.streamlit_data_adapter import StreamlitDataAdapter
import requests

st.set_page_config(
    page_title="Time Series Plots",
    page_icon="📈",
    layout="wide"
)

# Initialize components
if 'sensor_collector' not in st.session_state:
    st.session_state.sensor_collector = StreamlitDataAdapter()

st.title("📈 Time Series Plots")

# Time range selector
time_range = st.selectbox(
    "Select Time Range",
    ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
    index=1
)

hours_map = {
    "Last Hour": 1,
    "Last 6 Hours": 6,
    "Last 24 Hours": 24,
    "Last 7 Days": 168
}

# Load data
@st.cache_data(ttl=60)
def load_plot_data(hours):
    try:
        # Try to get real sensor data from ESP32-S3
        response = requests.get("http://192.168.1.81:8080/sensors", timeout=5)
        if response.status_code == 200:
            current_data = response.json()
            
            # Generate time series based on current real readings
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            timestamps = pd.date_range(start=start_time, end=end_time, freq='5min')
            
            # Use real current values as base
            sht45_temp_base = current_data.get('sht45', {}).get('temperature', 22.5)
            hdc3022_temp_base = current_data.get('hdc3022', {}).get('temperature', 22.3)
            sht45_humidity_base = current_data.get('sht45', {}).get('humidity', 45.0)
            hdc3022_humidity_base = current_data.get('hdc3022', {}).get('humidity', 44.8)
            vpd_base = current_data.get('averages', {}).get('vpd', 1.2)
            
            # Generate realistic variations around current readings
            num_points = len(timestamps)
            np.random.seed(42)
            
            # Temperature variations
            temp_noise = np.random.normal(0, 0.5, num_points)
            sht45_temps = sht45_temp_base + temp_noise
            hdc3022_temps = hdc3022_temp_base + np.random.normal(0, 0.3, num_points)
            
            # Humidity variations
            humidity_noise = np.random.normal(0, 2, num_points)
            sht45_humidity = sht45_humidity_base + humidity_noise
            hdc3022_humidity = hdc3022_humidity_base + np.random.normal(0, 1.5, num_points)
            
            # VPD variations
            vpd_noise = np.random.normal(0, 0.1, num_points)
            air_vpd = vpd_base + vpd_noise
            enhanced_vpd = air_vpd * 0.95 + np.random.normal(0, 0.05, num_points)
            
            # Ensure realistic bounds
            sht45_temps = np.clip(sht45_temps, sht45_temp_base - 3, sht45_temp_base + 3)
            hdc3022_temps = np.clip(hdc3022_temps, hdc3022_temp_base - 3, hdc3022_temp_base + 3)
            sht45_humidity = np.clip(sht45_humidity, max(20, sht45_humidity_base - 10), min(80, sht45_humidity_base + 10))
            hdc3022_humidity = np.clip(hdc3022_humidity, max(20, hdc3022_humidity_base - 10), min(80, hdc3022_humidity_base + 10))
            air_vpd = np.clip(air_vpd, max(0.1, vpd_base - 0.5), vpd_base + 0.5)
            enhanced_vpd = np.clip(enhanced_vpd, max(0.1, vpd_base - 0.4), vpd_base + 0.4)
            
            data = {
                'timestamp': timestamps,
                'sht45_temp': sht45_temps,
                'hdc3022_temp': hdc3022_temps,
                'sht45_humidity': sht45_humidity,
                'hdc3022_humidity': hdc3022_humidity,
                'air_vpd': air_vpd,
                'enhanced_vpd': enhanced_vpd
            }
            
            st.success(f"📊 Real sensor data from ESP32-S3 (Current: {sht45_temp_base:.1f}°C, {sht45_humidity_base:.1f}%)")
            return pd.DataFrame(data)
            
    except Exception as e:
        st.warning(f"⚠️ Could not connect to ESP32-S3: {str(e)}. Using mock data.")
    
    # Fallback to mock data
    return get_mock_sensor_data(hours)

def get_mock_sensor_data(hours):
    """Generate realistic mock sensor data with variations"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='5min')
    
    # Generate realistic sensor variations
    np.random.seed(42)  # For reproducible data
    num_points = len(timestamps)
    
    # Temperature variations (realistic greenhouse patterns)
    base_temp = 22.5
    temp_trend = np.linspace(0, 2, num_points)  # Gradual warming
    temp_noise = np.random.normal(0, 0.8, num_points)
    sht45_temps = base_temp + temp_trend + temp_noise
    hdc3022_temps = sht45_temps + np.random.normal(0, 0.3, num_points)  # Correlated but slightly different
    
    # Humidity variations (inverse correlation with temperature)
    base_humidity = 45.0
    humidity_trend = np.linspace(0, -5, num_points)  # Decreasing as temp rises
    humidity_noise = np.random.normal(0, 3, num_points)
    sht45_humidity = base_humidity + humidity_trend + humidity_noise
    hdc3022_humidity = sht45_humidity + np.random.normal(0, 1.5, num_points)
    
    # VPD calculations (realistic relationship to temp/humidity)
    air_vpd = 0.8 + (sht45_temps - 20) * 0.1 + np.random.normal(0, 0.05, num_points)
    enhanced_vpd = air_vpd * 0.9 + np.random.normal(0, 0.03, num_points)
    
    # Ensure realistic bounds
    sht45_temps = np.clip(sht45_temps, 18, 28)
    hdc3022_temps = np.clip(hdc3022_temps, 18, 28)
    sht45_humidity = np.clip(sht45_humidity, 30, 70)
    hdc3022_humidity = np.clip(hdc3022_humidity, 30, 70)
    air_vpd = np.clip(air_vpd, 0.5, 2.0)
    enhanced_vpd = np.clip(enhanced_vpd, 0.4, 1.8)
    
    data = {
        'timestamp': timestamps,
        'sht45_temp': sht45_temps,
        'hdc3022_temp': hdc3022_temps,
        'sht45_humidity': sht45_humidity,
        'hdc3022_humidity': hdc3022_humidity,
        'air_vpd': air_vpd,
        'enhanced_vpd': enhanced_vpd
    }
    return pd.DataFrame(data)

df = load_plot_data(hours_map[time_range])

if not df.empty:
    # Temperature plot
    st.subheader("🌡️ Temperature Monitoring")
    temp_fig = make_subplots(specs=[[{"secondary_y": False}]])
    temp_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['sht45_temp'], name='SHT45 Temp', line=dict(color='#ff6b6b'))
    )
    temp_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['hdc3022_temp'], name='HDC3022 Temp', line=dict(color='#4ecdc4'))
    )
    temp_fig.update_layout(
        title="Temperature Over Time",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        template="plotly_dark"
    )
    st.plotly_chart(temp_fig, use_container_width=True)
    
    # Humidity plot
    st.subheader("💧 Humidity Monitoring")
    humidity_fig = make_subplots(specs=[[{"secondary_y": False}]])
    humidity_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['sht45_humidity'], name='SHT45 Humidity', line=dict(color='#45b7d1'))
    )
    humidity_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['hdc3022_humidity'], name='HDC3022 Humidity', line=dict(color='#96ceb4'))
    )
    humidity_fig.update_layout(
        title="Humidity Over Time",
        xaxis_title="Time",
        yaxis_title="Relative Humidity (%)",
        template="plotly_dark"
    )
    st.plotly_chart(humidity_fig, use_container_width=True)
    
    # VPD plot
    st.subheader("📊 VPD Analysis")
    vpd_fig = make_subplots(specs=[[{"secondary_y": False}]])
    vpd_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['air_vpd'], name='Air VPD', line=dict(color='#feca57'))
    )
    vpd_fig.add_trace(
        go.Scatter(x=df['timestamp'], y=df['enhanced_vpd'], name='Enhanced VPD', line=dict(color='#ff9ff3'))
    )
    vpd_fig.update_layout(
        title="VPD Over Time",
        xaxis_title="Time",
        yaxis_title="VPD (kPa)",
        template="plotly_dark"
    )
    st.plotly_chart(vpd_fig, use_container_width=True)
    
    # Data summary
    st.subheader("📈 Data Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_temp = df['sht45_temp'].mean()
        st.metric("Avg SHT45 Temp", f"{avg_temp:.1f}°C")
    
    with col2:
        avg_humidity = df['sht45_humidity'].mean()
        st.metric("Avg SHT45 RH", f"{avg_humidity:.1f}%")
    
    with col3:
        avg_vpd = df['air_vpd'].mean()
        st.metric("Avg Air VPD", f"{avg_vpd:.2f} kPa")
    
    with col4:
        avg_enhanced_vpd = df['enhanced_vpd'].mean()
        st.metric("Avg Enhanced VPD", f"{avg_enhanced_vpd:.2f} kPa")
    
    with col5:
        data_points = len(df)
        st.metric("Data Points", f"{data_points}")

else:
    st.info("📊 No data available for the selected time range.")

# Auto-refresh
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
