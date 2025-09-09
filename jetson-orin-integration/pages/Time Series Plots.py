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
import csv
import os

st.set_page_config(
    page_title="Time Series Plots",
    page_icon="📈",
    layout="wide"
)

# Initialize components
if 'data_adapter' not in st.session_state:
    st.session_state.data_adapter = StreamlitDataAdapter()

st.title("📈 Time Series Plots")

# Time range selector
time_range = st.selectbox(
    "Select Time Range",
    ["Last 15 minutes", "Last 30 minutes", "Last Hour", "Last 2 Hours", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
    index=4
)

hours_map = {
    "Last 15 minutes": 0.25,
    "Last 30 minutes": 0.5,
    "Last Hour": 1,
    "Last 2 Hours": 2,
    "Last 6 Hours": 6,
    "Last 24 Hours": 24,
    "Last 7 Days": 168
}

def load_historical_data(hours):
    """Load historical data from CSV log file with robust parsing"""
    try:
        # Define CSV file path
        csv_file = "/home/lionel/jetson-greenhouse/data/jetson_sensor_data.csv"
        
        if not os.path.exists(csv_file):
            st.warning("⚠️ **NO CSV LOG FILE FOUND**")
            return None
        
        # Read CSV with flexible parsing to handle inconsistent column counts
        rows = []
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header:
                st.warning("⚠️ **EMPTY CSV FILE**")
                return None
                
            for line_num, row in enumerate(reader, 2):
                if len(row) >= 8:  # Ensure minimum required columns
                    # Extract the 8 essential columns in correct order
                    # Handle both 8-column (cleaned) and 17+ column (new logging) formats
                    if len(row) == 8:
                        # Original cleaned format: timestamp,sht45_temp,sht45_humidity,hdc3022_temp,hdc3022_humidity,foliage_temperature,air_vpd,enhanced_vpd
                        normalized_row = row
                    else:
                        # New logging format with extra columns - extract correct positions
                        # Based on recent data: timestamp,sht45_temp,sht45_humidity,hdc3022_temp,hdc3022_humidity,temp3,humidity3,temp4,temp5,temp6,temp7,vpd1,vpd2,vpd3,vpd4,unknown1,unknown2,foliage_temp
                        normalized_row = [
                            row[0],  # timestamp
                            row[1],  # sht45_temp
                            row[2],  # sht45_humidity  
                            row[3],  # hdc3022_temp
                            row[4],  # hdc3022_humidity
                            row[-1] if len(row) > 16 else row[5],  # foliage_temperature (last column in new format)
                            row[11] if len(row) > 11 else row[6],  # air_vpd (position 11 in new format)
                            row[12] if len(row) > 12 else row[7]   # enhanced_vpd (position 12 in new format)
                        ]
                    rows.append(normalized_row)
                else:
                    # Skip malformed rows
                    continue
        
        if not rows:
            st.warning("⚠️ **NO VALID DATA ROWS IN CSV**")
            return None
            
        # Create DataFrame with consistent column structure
        columns = ['timestamp', 'sht45_temp', 'sht45_humidity', 'hdc3022_temp', 
                  'hdc3022_humidity', 'foliage_temperature', 'air_vpd', 'enhanced_vpd']
        
        df = pd.DataFrame(rows, columns=columns)
        
        if df.empty:
            return None
            
        # Convert timestamp column
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            st.warning("⚠️ **NO VALID TIMESTAMPS IN CSV**")
            return None
        
        # Convert numeric columns
        numeric_columns = [col for col in df.columns if col != 'timestamp']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # Filter by time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        df = df[df['timestamp'] >= start_time]
        
        if df.empty:
            st.warning("⚠️ **NO HISTORICAL DATA** - No data in selected time range")
            return None
        
        # Get current real-time values for status display
        esp32_data = {}
            
        # Try ESP32-S3 sensor data for status
        try:
            esp32_response = requests.get("http://192.168.1.81:8080/sensors", timeout=3)
            if esp32_response.status_code == 200:
                esp32_data = esp32_response.json()
        except:
            pass
        
        current_time = datetime.now().strftime("%H:%M:%S")
            
        if esp32_data:
            esp32_status = f"ESP32-S3: {esp32_data.get('sht45', {}).get('temperature', 0):.1f}°C, {esp32_data.get('sht45', {}).get('humidity', 0):.1f}%"
        else:
            esp32_status = "ESP32-S3: Offline"
        
        # Always show historical data status
        data_points = len(df)
        time_span = df['timestamp'].max() - df['timestamp'].min()
        st.success(f"📊 **HISTORICAL DATA** - {data_points} points over {time_span} | Current: {esp32_status} | Last update: {current_time}")
        
        return df
        
    except Exception as e:
        st.error(f"❌ **ERROR LOADING HISTORICAL DATA**: {str(e)}")
        return None


df = load_historical_data(hours_map[time_range])

if df is not None and not df.empty:
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
