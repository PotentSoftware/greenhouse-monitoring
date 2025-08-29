#!/usr/bin/env python3
"""
Streamlit-based Time Series Dashboard for Jetson Greenhouse Monitoring
Replaces matplotlib plots with interactive Streamlit interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys
import os
import time
import json
import socket
import base64
from datetime import datetime, timedelta
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from streamlit_data_adapter import StreamlitDataAdapter
import logging
from logging.handlers import RotatingFileHandler
import requests
import numpy as np

# Configure page
st.set_page_config(
    page_title="Jetson Greenhouse Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.stButton > button {
    width: 100%;
}
.thermal-collection {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Color schemes for dark and light modes
COLORS = {
    'dark': {
        'sht45_temp': '#FF6B6B',      # Bright red
        'hdc3022_temp': '#4ECDC4',    # Bright teal
        'foliage_temp': '#45B7D1',    # Bright blue
        'sht45_humidity': '#96CEB4',   # Bright green
        'hdc3022_humidity': '#FFEAA7', # Bright yellow
        'air_vpd': '#DDA0DD',         # Bright purple
        'enhanced_vpd': '#FFA07A',    # Bright salmon
        'background': '#0E1117',
        'grid': '#262730'
    },
    'light': {
        'sht45_temp': '#E74C3C',      # Dark red
        'hdc3022_temp': '#16A085',    # Dark teal
        'foliage_temp': '#2980B9',    # Dark blue
        'sht45_humidity': '#27AE60',   # Dark green
        'hdc3022_humidity': '#F39C12', # Dark orange
        'air_vpd': '#8E44AD',         # Dark purple
        'enhanced_vpd': '#E67E22',    # Dark orange-red
        'background': '#FFFFFF',
        'grid': '#E1E5E9'
    }
}

class StreamlitDataLogger:
    """Handles data logging with 7-day rollover"""
    
    def __init__(self, log_dir="/home/lionel/jetson-greenhouse/data"):
        self.log_dir = log_dir
        self.log_file = os.path.join(log_dir, "streamlit_sensor_data.csv")
        self.setup_logging()
        
    def setup_logging(self):
        """Setup rotating file handler for 7-day data retention"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create rotating file handler (7 days * 24 hours * 720 entries/hour = ~120,960 entries)
        # At 5-second intervals: 7 days = 120,960 entries
        max_bytes = 50 * 1024 * 1024  # 50MB per file
        backup_count = 3  # Keep 3 backup files (total ~7 days)
        
        self.file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        # Setup CSV header if file doesn't exist
        if not os.path.exists(self.log_file):
            self.write_csv_header()
    
    def write_csv_header(self):
        """Write CSV header"""
        header = "timestamp,sht45_temp,hdc3022_temp,foliage_temp,sht45_humidity,hdc3022_humidity,air_vpd,enhanced_vpd\n"
        with open(self.log_file, 'w') as f:
            f.write(header)
    
    def log_data(self, data):
        """Log sensor data to CSV"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Filter out zero foliage temperatures (invalid readings)
            foliage_temp = data.get('foliage_temp', 0)
            if foliage_temp <= 0:
                foliage_temp = np.nan
            
            row = f"{timestamp},{data.get('sht45_temp', 0)},{data.get('hdc3022_temp', 0)},{foliage_temp},{data.get('sht45_humidity', 0)},{data.get('hdc3022_humidity', 0)},{data.get('air_vpd', 0)},{data.get('enhanced_vpd', 0)}\n"
            
            with open(self.log_file, 'a') as f:
                f.write(row)
                
        except Exception as e:
            st.error(f"Logging error: {e}")


def load_historical_data(data_logger, hours=2):
    """Load historical data from CSV file"""
    try:
        if os.path.exists(data_logger.log_file):
            # Check if file is empty or has no data
            if os.path.getsize(data_logger.log_file) == 0:
                return pd.DataFrame()
            
            # Define column names since CSV has no headers
            column_names = ['timestamp', 'sht45_temp', 'hdc3022_temp', 'foliage_temp', 
                          'sht45_humidity', 'hdc3022_humidity', 'air_vpd', 'enhanced_vpd']
            
            df = pd.read_csv(data_logger.log_file, names=column_names)
            
            # Check if DataFrame is empty
            if df.empty:
                return pd.DataFrame()
            
            # Rename foliage_temp to foliage_temperature for plotter compatibility
            df = df.rename(columns={'foliage_temp': 'foliage_temperature'})
                
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter to last N hours
            cutoff_time = datetime.now() - timedelta(hours=hours)
            df = df[df['timestamp'] >= cutoff_time]
            
            # Filter out zero foliage temperatures
            df.loc[df['foliage_temperature'] <= 0, 'foliage_temperature'] = np.nan
            
            return df.sort_values('timestamp')
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading historical data: {e}")
        return pd.DataFrame()

def create_temperature_plot(df, theme):
    """Create temperature plot with SHT45, HDC3022, and Foliage temperatures"""
    colors = COLORS[theme]
    
    fig = go.Figure()
    
    if not df.empty:
        # SHT45 Temperature
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['sht45_temp'],
            mode='lines+markers',
            name='SHT45 Temperature',
            line=dict(color=colors['sht45_temp'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>SHT45 Temperature</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
        ))
        
        # HDC3022 Temperature
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['hdc3022_temp'],
            mode='lines+markers',
            name='HDC3022 Temperature',
            line=dict(color=colors['hdc3022_temp'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>HDC3022 Temperature</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
        ))
        
        # Foliage Temperature (filtered for valid readings)
        if 'foliage_temperature' in df.columns:
            valid_foliage = df.dropna(subset=['foliage_temperature'])
            if not valid_foliage.empty:
                fig.add_trace(go.Scatter(
                    x=valid_foliage['timestamp'],
                    y=valid_foliage['foliage_temperature'],
                    mode='lines+markers',
                    name='Foliage Temperature',
                    line=dict(color=colors['foliage_temp'], width=3),
                    marker=dict(size=4),
                    hovertemplate='<b>Foliage Temperature</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
                ))
    
    fig.update_layout(
        title="🌡️ Temperature Monitoring",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        hovermode='closest',
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color='white' if theme == 'dark' else 'black',
        xaxis=dict(
            gridcolor=colors['grid'],
            showgrid=True,
            dtick=5000,  # 5 seconds in milliseconds
            minor=dict(
                dtick=5000,
                gridcolor='rgba(128, 128, 128, 0.2)',
                gridwidth=0.5,
                showgrid=True
            )
        ),
        yaxis=dict(
            gridcolor=colors['grid'],
            range=[15, 32],
            dtick=2
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Configure toolbar with pan and zoom
    fig.update_layout(
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0)',
            color='white' if theme == 'dark' else 'black',
            activecolor='lightblue'
        )
    )
    
    return fig

def create_humidity_plot(df, theme):
    """Create humidity plot with SHT45 and HDC3022 humidity"""
    colors = COLORS[theme]
    
    fig = go.Figure()
    
    if not df.empty:
        # SHT45 Humidity
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['sht45_humidity'],
            mode='lines+markers',
            name='SHT45 Humidity',
            line=dict(color=colors['sht45_humidity'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>SHT45 Humidity</b><br>Time: %{x}<br>RH: %{y:.1f}%<extra></extra>'
        ))
        
        # HDC3022 Humidity
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['hdc3022_humidity'],
            mode='lines+markers',
            name='HDC3022 Humidity',
            line=dict(color=colors['hdc3022_humidity'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>HDC3022 Humidity</b><br>Time: %{x}<br>RH: %{y:.1f}%<extra></extra>'
        ))
    
    fig.update_layout(
        title="💧 Humidity Monitoring",
        xaxis_title="Time",
        yaxis_title="Relative Humidity (%)",
        hovermode='closest',
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color='white' if theme == 'dark' else 'black',
        xaxis=dict(
            gridcolor=colors['grid'],
            showgrid=True,
            dtick=5000,  # 5 seconds in milliseconds
            minor=dict(
                dtick=5000,
                gridcolor='rgba(128, 128, 128, 0.2)',
                gridwidth=0.5,
                showgrid=True
            )
        ),
        yaxis=dict(
            gridcolor=colors['grid'],
            range=[40, 85],
            dtick=5
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Configure toolbar with pan and zoom
    fig.update_layout(
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0)',
            color='white' if theme == 'dark' else 'black',
            activecolor='lightblue'
        )
    )
    
    return fig

def create_vpd_plot(df, theme):
    """Create VPD plot with Air VPD and Enhanced VPD (using SHT45 humidity)"""
    colors = COLORS[theme]
    
    fig_temp = go.Figure()
    
    # Add temperature traces
    fig_temp.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['sht45_temp'],
        mode='lines+markers',
        name='Air Temperature',
        line=dict(color='#FF6B6B', width=2),
        marker=dict(size=4),
        hovertemplate='<b>Air Temperature</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
    ))
    
    fig_temp.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['foliage_temperature'],
        mode='lines+markers',
        name='Foliage Temperature',
        line=dict(color='#4ECDC4', width=2),
        marker=dict(size=4),
        hovertemplate='<b>Foliage Temperature</b><br>Time: %{x}<br>Temp: %{y:.1f}°C<extra></extra>'
    ))
    
    fig_temp.update_layout(
        title='🌡️ Temperature Monitoring',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        hovermode='closest',
        template='plotly_dark' if theme == 'dark' else 'plotly_white',
        height=400,
        showlegend=True,
        legend=dict(x=0.02, y=0.98),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.3)',
            dtick=5000,  # 5 seconds in milliseconds
            minor=dict(
                dtick=5000,
                gridcolor='rgba(128, 128, 128, 0.2)',
                gridwidth=0.5,
                showgrid=True
            )
        )
    )
    
    fig = go.Figure()
    
    if not df.empty:
        # Air VPD
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['air_vpd'],
            mode='lines+markers',
            name='Air VPD',
            line=dict(color=colors['air_vpd'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>Air VPD</b><br>Time: %{x}<br>VPD: %{y:.2f} kPa<extra></extra>'
        ))
        
        # Enhanced VPD
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['enhanced_vpd'],
            mode='lines+markers',
            name='Enhanced VPD',
            line=dict(color=colors['enhanced_vpd'], width=3),
            marker=dict(size=4),
            hovertemplate='<b>Enhanced VPD</b><br>Time: %{x}<br>VPD: %{y:.2f} kPa<extra></extra>'
        ))
    
    fig.update_layout(
        title="📊 VPD Analysis (SHT45-based)",
        xaxis_title="Time",
        yaxis_title="VPD (kPa)",
        hovermode='closest',
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color='white' if theme == 'dark' else 'black',
        xaxis=dict(
            gridcolor=colors['grid'],
            showgrid=True,
            dtick=5000,  # 5 seconds in milliseconds
            minor=dict(
                dtick=5000,
                gridcolor='rgba(128, 128, 128, 0.2)',
                gridwidth=0.5,
                showgrid=True
            )
        ),
        yaxis=dict(
            gridcolor=colors['grid'],
            range=[1.0, 1.5],
            dtick=0.1
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Configure toolbar with pan and zoom
    fig.update_layout(
        modebar=dict(
            orientation='v',
            bgcolor='rgba(0,0,0,0)',
            color='white' if theme == 'dark' else 'black',
            activecolor='lightblue'
        )
    )
    
    return fig

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    if 'data_logger' not in st.session_state:
        st.session_state.data_logger = StreamlitDataLogger()
    
    if 'sensor_collector' not in st.session_state:
        st.session_state.sensor_collector = StreamlitDataAdapter()
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    # Track if a thermal image collection is in progress to avoid auto-refresh interrupts
    if 'collecting' not in st.session_state:
        st.session_state.collecting = False
    
    # Sidebar controls
    st.sidebar.title("🌱 Greenhouse Monitor")
    
    # Sidebar separator
    st.sidebar.markdown("---")
    
    # Theme selection
    theme = st.sidebar.selectbox(
        "🎨 Theme",
        ["dark", "light"],
        index=0
    )
    
    # Time range selection
    time_range = st.sidebar.selectbox(
        "⏰ Time Range",
        ["30 minutes", "1 hour", "2 hours", "4 hours", "8 hours"],
        index=2
    )
    
    hours_map = {
        "30 minutes": 0.5,
        "1 hour": 1,
        "2 hours": 2,
        "4 hours": 4,
        "8 hours": 8
    }
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=True)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.rerun()
    
    # Main title and Tools popover
    top_col1, top_col2 = st.columns([3,1])
    with top_col1:
        st.title("🌱 Jetson Greenhouse Time Series Dashboard")
    with top_col2:
        pop = st.popover("Tools")
        with pop:
            st.page_link("pages/Collect Images.py", label="📷 Collect Images")
            st.page_link("pages/Analyse Collection.py", label="📊 Analyse Collection")
            st.page_link("pages/Time Series Plots.py", label="📈 Time Series Plots")
            st.page_link("pages/Live Thermal Camera.py", label="🌡️ Live Thermal Camera")
            if st.button("💾 Export Data"):
                st.markdown("[💾 Export Data](http://192.168.1.75:8082/download/csv)", unsafe_allow_html=True)
            if st.button("📊 JSON API"):
                st.markdown("[📊 JSON API](http://192.168.1.75:8082/api/sensors)", unsafe_allow_html=True)
    
    # Status indicators
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📡 Status", "Online", delta="Connected")
    
    with col2:
        st.metric("⏱️ Update Rate", "5 seconds", delta="Real-time")
    
    with col3:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("🕐 Current Time", current_time)
    
    # Load historical data
    df = load_historical_data(st.session_state.data_logger, hours_map[time_range])
    
    # Collect new data point if auto-refresh is enabled and not currently collecting images
    if auto_refresh and not st.session_state.collecting:
        now = datetime.now()
        if (now - st.session_state.last_update).total_seconds() >= 5:
            # Get new sensor data from Jetson server
            new_data = st.session_state.sensor_collector.get_sensor_data()
            if new_data is None:
                # Fallback to mock data if server unavailable
                new_data = st.session_state.sensor_collector.get_mock_data()
            
            if new_data:
                st.session_state.data_logger.log_data(new_data)
                st.session_state.last_update = now
                time.sleep(1)  # Brief pause
                st.rerun()
    
    # Current Sensor Readings
    st.subheader("🌡️ Current Sensor Readings")
    
    # Get latest sensor data from ESP32-S3
    latest_data = st.session_state.sensor_collector.get_sensor_data()
    if latest_data is None:
        latest_data = st.session_state.sensor_collector.get_mock_data()
    
    if latest_data:
        # Display current readings in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌡️ SHT45 Temperature", f"{latest_data.get('sht45_temp', 0):.1f}°C")
            st.metric("🌡️ HDC3022 Temperature", f"{latest_data.get('hdc3022_temp', 0):.1f}°C")
        
        with col2:
            st.metric("💧 SHT45 Humidity", f"{latest_data.get('sht45_humidity', 0):.1f}%")
            st.metric("💧 HDC3022 Humidity", f"{latest_data.get('hdc3022_humidity', 0):.1f}%")
        
        with col3:
            st.metric("📊 Air VPD", f"{latest_data.get('air_vpd', 0):.2f} kPa")
            st.metric("📊 Enhanced VPD", f"{latest_data.get('enhanced_vpd', 0):.2f} kPa")
        
        with col4:
            st.metric("🌡️ Thermal Min", f"{latest_data.get('thermal_min', 0):.1f}°C")
            st.metric("🌡️ Thermal Max", f"{latest_data.get('thermal_max', 0):.1f}°C")
    
    # Time series plots removed from main dashboard - available via Tools menu
    
    # Thermal Image Collection UI removed from main page; use Tools → pages instead.
    
    # Footer
    st.markdown("---")
    st.markdown("**🌱 Jetson Orin Nano Greenhouse Monitoring System** | Data logged with 7-day rollover")

def collect_thermal_images(num_images: int, interval_seconds: int):
    """Collect thermal images and save to timestamped directory"""
    try:
        # Mark collection in progress to pause auto-refresh reruns
        st.session_state.collecting = True
        
        # Quick connectivity check before starting
        ok, msg = test_thermal_camera_connection()
        if not ok:
            st.error(f"Cannot start collection: {msg}")
            return
        # Create timestamped directory
        desktop_path = Path.home() / "Desktop"
        desktop_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        collection_dir = desktop_path / f"thermal_collection_{timestamp}"
        collection_dir.mkdir(exist_ok=True)
        
        st.success(f"📁 Created collection directory: {collection_dir}")
        
        # Collection metadata
        metadata = {
            "collection_start": datetime.now().isoformat(),
            "num_images_requested": num_images,
            "interval_seconds": interval_seconds,
            "collection_directory": str(collection_dir),
            "images_captured": [],
            "capture_errors": [],
            "thermal_camera_config": {
                "host": "192.168.1.130",
                "port": 5001,
                "resolution": "160x120",
                "thermal_resolution": 0.01,
                "kelvin_offset": 273.15
            }
        }
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        captured_images = []
        
        for i in range(num_images):
            progress = (i + 1) / num_images
            progress_bar.progress(progress)
            status_text.text(f"📸 Capturing image {i+1}/{num_images}...")
            
            # Capture thermal image
            image_data = capture_single_thermal_image()
            
            if image_data is not None:
                thermal_array = image_data['thermal_array']
                stats = image_data['stats']
                
                # Generate filename with timestamp and sequence number
                img_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
                filename = f"thermal_image_{i+1:02d}_{img_timestamp}.npy"
                filepath = collection_dir / filename
                
                try:
                    # Save as .npy file
                    np.save(filepath, thermal_array)
                    
                    # Add to metadata
                    image_stats = {
                        "filename": filename,
                        "capture_time": datetime.now().isoformat(),
                        "sequence_number": i + 1,
                        "image_shape": thermal_array.shape,
                        **stats
                    }
                    
                    metadata["images_captured"].append(image_stats)
                    captured_images.append(thermal_array)
                    
                    st.success(f"✅ Saved {filename} - Temp range: {stats['min_temp']:.1f}°C to {stats['max_temp']:.1f}°C")
                    
                except Exception as e:
                    error_msg = f"Failed to save image {i+1}: {e}"
                    st.error(f"❌ {error_msg}")
                    metadata["capture_errors"].append({
                        "sequence_number": i + 1,
                        "error": error_msg,
                        "timestamp": datetime.now().isoformat()
                    })
            else:
                error_msg = f"Failed to capture image {i+1}"
                st.error(f"❌ {error_msg}")
                metadata["capture_errors"].append({
                    "sequence_number": i + 1,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait for next capture (except for last image)
            if i < num_images - 1:
                status_text.text(f"⏱️ Waiting {interval_seconds} seconds for next capture...")
                time.sleep(interval_seconds)
        
        # Finalize metadata
        metadata["collection_end"] = datetime.now().isoformat()
        metadata["images_successfully_captured"] = len(metadata["images_captured"])
        metadata["total_errors"] = len(metadata["capture_errors"])
        
        # Save metadata as JSON
        metadata_file = collection_dir / "collection_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            st.success(f"📋 Saved collection metadata: {metadata_file}")
        except Exception as e:
            st.error(f"❌ Failed to save metadata: {e}")
        
        # Create summary file
        summary_file = collection_dir / "README.txt"
        try:
            with open(summary_file, 'w') as f:
                f.write(f"Thermal Image Collection Summary\n")
                f.write(f"================================\n\n")
                f.write(f"Collection Date: {metadata['collection_start']}\n")
                f.write(f"Images Requested: {metadata['num_images_requested']}\n")
                f.write(f"Images Captured: {metadata['images_successfully_captured']}\n")
                f.write(f"Capture Interval: {metadata['interval_seconds']} seconds\n")
                f.write(f"Total Errors: {metadata['total_errors']}\n\n")
                f.write(f"Files in this directory:\n")
                f.write(f"- thermal_image_XX_YYYYMMDD_HHMMSS_mmm.npy: Raw thermal data arrays\n")
                f.write(f"- collection_metadata.json: Detailed collection metadata\n")
                f.write(f"- README.txt: This summary file\n\n")
                f.write(f"Image Format:\n")
                f.write(f"- NumPy arrays in .npy format\n")
                f.write(f"- Shape: 120x160 pixels\n")
                f.write(f"- Data type: float64 (temperature in Celsius)\n")
                f.write(f"- Negative values indicate faulty pixels\n\n")
                f.write(f"Usage:\n")
                f.write(f"import numpy as np\n")
                f.write(f"thermal_data = np.load('thermal_image_01_YYYYMMDD_HHMMSS_mmm.npy')\n")
            
            st.success(f"📄 Created summary file: {summary_file}")
        except Exception as e:
            st.error(f"❌ Failed to create summary file: {e}")
        
        # Final status
        progress_bar.progress(1.0)
        status_text.text(f"🎉 Collection complete! {metadata['images_successfully_captured']}/{num_images} images saved")
        
        st.balloons()
        
    except Exception as e:
        st.error(f"❌ Collection failed: {e}")
    finally:
        # Always clear the collecting flag
        st.session_state.collecting = False

def capture_single_thermal_image():
    """Capture a single thermal image from tCam-Mini"""
    try:
        # Connect to tCam-Mini
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect(("192.168.1.130", 5001))
        
        # Send command with STX/ETX delimiters
        command = json.dumps({"cmd": "get_image"}) + "\n"
        stx_command = b"\x02" + command.encode() + b"\x03"
        sock.sendall(stx_command)
        
        # Receive response until ETX seen
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
            # Extract JSON between STX/ETX
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
                # Process thermal image
                img_b64 = thermal_data['radiometric']
                try:
                    img_data = base64.b64decode(img_b64)
                except Exception as de:
                    st.error(f"Base64 decode error: {de}\nRadiometric (truncated): {str(img_b64)[:80]}...")
                    return None
                thermal_array = np.frombuffer(img_data, dtype=np.uint16)
                thermal_raw = thermal_array.reshape((120, 160))
                
                # Convert to Celsius
                thermal_celsius = (thermal_raw * 0.01) - 273.15
                
                # Filter negative pixels (faulty readings)
                valid_pixels = thermal_celsius[thermal_celsius > 0]
                
                if len(valid_pixels) > 0:
                    # Calculate comprehensive statistics
                    min_temp = float(np.min(valid_pixels))
                    max_temp = float(np.max(valid_pixels))
                    avg_temp = float(np.mean(valid_pixels))
                    median_temp = float(np.median(valid_pixels))
                    
                    # Calculate modal temperature (most frequent value)
                    hist, bin_edges = np.histogram(valid_pixels, bins=50)
                    modal_bin = np.argmax(hist)
                    modal_temp = float((bin_edges[modal_bin] + bin_edges[modal_bin + 1]) / 2)
                    
                    # Negative pixel filtering stats
                    total_pixels = thermal_celsius.size
                    negative_pixels = np.sum(thermal_celsius <= 0)
                    filtered_pixels = total_pixels - negative_pixels
                    
                    return {
                        'thermal_array': thermal_celsius,
                        'stats': {
                            "min_temp": min_temp,
                            "max_temp": max_temp,
                            "avg_temp": avg_temp,
                            "median_temp": median_temp,
                            "modal_temp": modal_temp,
                            "total_pixels": int(total_pixels),
                            "negative_pixels": int(negative_pixels),
                            "filtered_pixels": int(filtered_pixels)
                        }
                    }
            else:
                st.error("Camera response missing 'radiometric' field")
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error capturing thermal image: {e}")
        return None

def test_thermal_camera_connection():
    """Quick connectivity check to tCam-Mini returning (ok, message)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        sock.connect(("192.168.1.130", 5001))
        # send a lightweight get_image and read a small header
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

if __name__ == "__main__":
    main()
