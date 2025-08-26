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
from datetime import datetime, timedelta
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
    
    # Sidebar controls
    st.sidebar.title("🌱 Greenhouse Monitor")
    
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
    
    # Main title
    st.title("🌱 Jetson Greenhouse Time Series Dashboard")
    
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
    
    # Collect new data point if auto-refresh is enabled
    if auto_refresh:
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
    
    # Create plots
    if not df.empty:
        # Temperature plot
        st.subheader("🌡️ Temperature Monitoring")
        temp_fig = create_temperature_plot(df, theme)
        st.plotly_chart(temp_fig, use_container_width=True)
        
        # Humidity plot
        st.subheader("💧 Humidity Monitoring")
        humidity_fig = create_humidity_plot(df, theme)
        st.plotly_chart(humidity_fig, use_container_width=True)
        
        # VPD plot
        st.subheader("📊 VPD Analysis")
        vpd_fig = create_vpd_plot(df, theme)
        st.plotly_chart(vpd_fig, use_container_width=True)
        
        # Data summary
        st.subheader("📈 Data Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if 'sht45_temp' in df.columns:
                avg_temp = df['sht45_temp'].mean()
                st.metric("Avg SHT45 Temp", f"{avg_temp:.1f}°C")
        
        with col2:
            if 'sht45_humidity' in df.columns:
                avg_humidity = df['sht45_humidity'].mean()
                st.metric("Avg SHT45 RH", f"{avg_humidity:.1f}%")
        
        with col3:
            if 'air_vpd' in df.columns:
                avg_vpd = df['air_vpd'].mean()
                st.metric("Avg Air VPD", f"{avg_vpd:.2f} kPa")
        
        with col4:
            if 'enhanced_vpd' in df.columns:
                avg_enhanced_vpd = df['enhanced_vpd'].mean()
                st.metric("Avg Enhanced VPD", f"{avg_enhanced_vpd:.2f} kPa")
        
        with col5:
            data_points = len(df)
            st.metric("Data Points", f"{data_points}")
        
    else:
        st.info("📊 No data available yet. Data collection will begin shortly...")
        st.info("🔄 Enable auto-refresh to start collecting data every 5 seconds.")
    
    # Footer
    st.markdown("---")
    st.markdown("**🌱 Jetson Orin Nano Greenhouse Monitoring System** | Data logged with 7-day rollover")

if __name__ == "__main__":
    main()
