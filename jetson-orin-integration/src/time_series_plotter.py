#!/usr/bin/env python3
"""
Time Series Plotter for Jetson Greenhouse Monitoring
Creates real-time plots of temperature, humidity, VPD, and foliage data
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os
import logging
from typing import Dict, List, Optional
import io
import base64
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

class TimeSeriesPlotter:
    def __init__(self, data_file: str, max_hours: int = 2):
        """
        Initialize time series plotter
        
        Args:
            data_file: Path to CSV data file
            max_hours: Maximum hours of data to display
        """
        self.data_file = data_file
        self.max_hours = max_hours
        self.logger = logging.getLogger(__name__)
        
        # Set matplotlib style for dark theme
        plt.style.use('dark_background')
        
        # Color scheme for different data series
        self.colors = {
            'sht45_temp': '#ff6b6b',
            'hdc3022_temp': '#4ecdc4', 
            'foliage_temp': '#45b7d1',
            'sht45_humidity': '#96ceb4',
            'hdc3022_humidity': '#feca57',
            'air_vpd': '#ff9ff3',
            'enhanced_vpd_foliage': '#54a0ff'
        }
        
        # Y-axis scaling options
        self.y_axis_modes = {
            'auto': 'Auto Scale',
            'tight': 'Tight Fit', 
            'fixed': 'Fixed Range',
            'data_range': 'Data Range + Margin'
        }
        
    def load_recent_data(self) -> Optional[pd.DataFrame]:
        """Load recent data from CSV file"""
        try:
            if not os.path.exists(self.data_file):
                self.logger.warning(f"Data file not found: {self.data_file}")
                return None
                
            # Read CSV data
            df = pd.read_csv(self.data_file)
            
            if df.empty:
                return None
                
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter to recent data only
            cutoff_time = datetime.now() - timedelta(hours=self.max_hours)
            df = df[df['timestamp'] >= cutoff_time]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return None
    
    def apply_y_axis_scaling(self, ax, data_series: List[pd.Series], y_mode: str = 'auto', 
                            fixed_range: tuple = None, margin_percent: float = 10.0):
        """
        Apply y-axis scaling based on specified mode
        
        Args:
            ax: Matplotlib axis object
            data_series: List of pandas Series containing plot data
            y_mode: Scaling mode ('auto', 'tight', 'fixed', 'data_range')
            fixed_range: Tuple of (min, max) for fixed mode
            margin_percent: Percentage margin for data_range mode
        """
        if y_mode == 'auto':
            # Let matplotlib auto-scale
            ax.relim()
            ax.autoscale_view()
        elif y_mode == 'tight':
            # Tight fit to data with minimal padding
            all_data = pd.concat([s.dropna() for s in data_series if not s.empty])
            if not all_data.empty:
                y_min, y_max = all_data.min(), all_data.max()
                padding = (y_max - y_min) * 0.02  # 2% padding
                ax.set_ylim(y_min - padding, y_max + padding)
        elif y_mode == 'fixed' and fixed_range:
            # Fixed range specified by user
            ax.set_ylim(fixed_range[0], fixed_range[1])
        elif y_mode == 'data_range':
            # Data range with specified margin
            all_data = pd.concat([s.dropna() for s in data_series if not s.empty])
            if not all_data.empty:
                y_min, y_max = all_data.min(), all_data.max()
                margin = (y_max - y_min) * (margin_percent / 100.0)
                ax.set_ylim(y_min - margin, y_max + margin)

    def create_temperature_plot(self, df: pd.DataFrame, y_mode: str = 'data_range') -> str:
        """Create temperature time series plot"""
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#2a2a2a')
        
        # Plot temperature data
        if 'sht45_temp' in df.columns:
            ax.plot(df['timestamp'], df['sht45_temp'], 
                   color=self.colors['sht45_temp'], linewidth=2, 
                   label='SHT45 Temperature', marker='o', markersize=3)
        
        if 'hdc3022_temp' in df.columns:
            ax.plot(df['timestamp'], df['hdc3022_temp'], 
                   color=self.colors['hdc3022_temp'], linewidth=2, 
                   label='HDC3022 Temperature', marker='s', markersize=3)
        
        if 'foliage_temperature' in df.columns:
            ax.plot(df['timestamp'], df['foliage_temperature'], 
                   color=self.colors['foliage_temp'], linewidth=2, 
                   label='Foliage Temperature', marker='^', markersize=3)
        
        ax.set_title('🌡️ Temperature Trends', fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel('Temperature (°C)', fontsize=12, color='white')
        ax.legend(loc='upper left', facecolor='#3a3a3a', edgecolor='white')
        ax.grid(True, alpha=0.3)
        
        # Apply y-axis scaling
        data_series = []
        if 'sht45_temp' in df.columns:
            data_series.append(df['sht45_temp'])
        if 'hdc3022_temp' in df.columns:
            data_series.append(df['hdc3022_temp'])
        if 'foliage_temperature' in df.columns:
            data_series.append(df['foliage_temperature'])
        
        self.apply_y_axis_scaling(ax, data_series, y_mode)
        
        # Format x-axis with date and time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Auto-scroll to show latest data on the right
        if not df.empty:
            x_min = df['timestamp'].min()
            x_max = df['timestamp'].max()
            x_range = x_max - x_min
            # Extend x-axis by 5% on the right for future data points
            ax.set_xlim(x_min, x_max + x_range * 0.05)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def create_humidity_plot(self, df: pd.DataFrame, y_mode: str = 'data_range') -> str:
        """Create humidity time series plot"""
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#2a2a2a')
        
        # Plot humidity data
        if 'sht45_humidity' in df.columns:
            ax.plot(df['timestamp'], df['sht45_humidity'], 
                   color=self.colors['sht45_humidity'], linewidth=2, 
                   label='SHT45 Humidity', marker='o', markersize=3)
        
        if 'hdc3022_humidity' in df.columns:
            ax.plot(df['timestamp'], df['hdc3022_humidity'], 
                   color=self.colors['hdc3022_humidity'], linewidth=2, 
                   label='HDC3022 Humidity', marker='s', markersize=3)
        
        ax.set_title('💧 Relative Humidity Trends', fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel('Relative Humidity (%RH)', fontsize=12, color='white')
        ax.legend(loc='upper left', facecolor='#3a3a3a', edgecolor='white')
        ax.grid(True, alpha=0.3)
        
        # Apply y-axis scaling (override default 0-100 for humidity if needed)
        if y_mode != 'auto':
            data_series = []
            if 'sht45_humidity' in df.columns:
                data_series.append(df['sht45_humidity'])
            if 'hdc3022_humidity' in df.columns:
                data_series.append(df['hdc3022_humidity'])
            
            if y_mode == 'fixed':
                self.apply_y_axis_scaling(ax, data_series, y_mode, fixed_range=(0, 100))
            else:
                self.apply_y_axis_scaling(ax, data_series, y_mode)
        else:
            ax.set_ylim(0, 100)
        
        # Format x-axis with date and time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Auto-scroll to show latest data on the right
        if not df.empty:
            x_min = df['timestamp'].min()
            x_max = df['timestamp'].max()
            x_range = x_max - x_min
            # Extend x-axis by 5% on the right for future data points
            ax.set_xlim(x_min, x_max + x_range * 0.05)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def create_vpd_plot(self, df: pd.DataFrame, y_mode: str = 'data_range') -> str:
        """Create VPD time series plot"""
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#2a2a2a')
        
        # Plot VPD data
        if 'air_vpd' in df.columns:
            ax.plot(df['timestamp'], df['air_vpd'], 
                   color=self.colors['air_vpd'], linewidth=2, 
                   label='Air VPD', marker='o', markersize=3)
        
        if 'enhanced_vpd_foliage' in df.columns:
            ax.plot(df['timestamp'], df['enhanced_vpd_foliage'], 
                   color=self.colors['enhanced_vpd_foliage'], linewidth=2, 
                   label='Enhanced VPD (Foliage + SHT45)', marker='^', markersize=3)
        
        # Add VPD zones
        ax.axhspan(0.8, 1.2, alpha=0.2, color='green', label='Optimal VPD Zone')
        ax.axhspan(0.4, 0.8, alpha=0.1, color='yellow', label='Low VPD Zone')
        ax.axhspan(1.2, 1.6, alpha=0.1, color='orange', label='High VPD Zone')
        
        ax.set_title('📊 VPD Trends', fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel('VPD (kPa)', fontsize=12, color='white')
        ax.legend(loc='upper left', facecolor='#3a3a3a', edgecolor='white')
        ax.grid(True, alpha=0.3)
        
        # Apply y-axis scaling
        data_series = []
        if 'air_vpd' in df.columns:
            data_series.append(df['air_vpd'])
        if 'enhanced_vpd_foliage' in df.columns:
            data_series.append(df['enhanced_vpd_foliage'])
        
        if y_mode == 'fixed':
            self.apply_y_axis_scaling(ax, data_series, y_mode, fixed_range=(0, 2.0))
        else:
            self.apply_y_axis_scaling(ax, data_series, y_mode)
        
        # Format x-axis with date and time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Auto-scroll to show latest data on the right
        if not df.empty:
            x_min = df['timestamp'].min()
            x_max = df['timestamp'].max()
            x_range = x_max - x_min
            # Extend x-axis by 5% on the right for future data points
            ax.set_xlim(x_min, x_max + x_range * 0.05)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def create_foliage_plot(self, df: pd.DataFrame, y_mode: str = 'data_range') -> str:
        """Create foliage temperature plot with segmentation info"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        fig.patch.set_facecolor('#1a1a1a')
        ax1.set_facecolor('#2a2a2a')
        ax2.set_facecolor('#2a2a2a')
        
        # Plot foliage temperature
        if 'foliage_temperature' in df.columns:
            ax1.plot(df['timestamp'], df['foliage_temperature'], 
                    color=self.colors['foliage_temp'], linewidth=2, 
                    label='Foliage Temperature', marker='o', markersize=3)
        
        ax1.set_title('🌿 Foliage Temperature Analysis', fontsize=16, color='white', pad=20)
        ax1.set_ylabel('Temperature (°C)', fontsize=12, color='white')
        ax1.legend(loc='upper left', facecolor='#3a3a3a', edgecolor='white')
        ax1.grid(True, alpha=0.3)
        
        # Apply y-axis scaling for temperature plot
        if 'foliage_temperature' in df.columns:
            # Use fixed range for foliage temperature (20-30°C) for better visualization
            if y_mode == 'data_range':
                self.apply_y_axis_scaling(ax1, [df['foliage_temperature']], y_mode, margin_percent=15.0)
            else:
                self.apply_y_axis_scaling(ax1, [df['foliage_temperature']], y_mode)
        
        # Plot segmentation ratio if available
        if 'segmentation_ratio' in df.columns:
            ax2.plot(df['timestamp'], df['segmentation_ratio'] * 100, 
                    color='#f39c12', linewidth=2, 
                    label='Foliage Coverage', marker='s', markersize=3)
        
        ax2.set_xlabel('Time', fontsize=12, color='white')
        ax2.set_ylabel('Coverage (%)', fontsize=12, color='white')
        ax2.legend(loc='upper left', facecolor='#3a3a3a', edgecolor='white')
        ax2.grid(True, alpha=0.3)
        
        # Apply y-axis scaling for coverage plot
        if 'segmentation_ratio' in df.columns:
            coverage_data = df['segmentation_ratio'] * 100
            if y_mode == 'fixed':
                self.apply_y_axis_scaling(ax2, [coverage_data], y_mode, fixed_range=(0, 100))
            else:
                self.apply_y_axis_scaling(ax2, [coverage_data], y_mode)
        else:
            ax2.set_ylim(0, 100)
        
        # Format x-axis with date and time
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Auto-scroll to show latest data on the right
        if not df.empty:
            x_min = df['timestamp'].min()
            x_max = df['timestamp'].max()
            x_range = x_max - x_min
            # Extend x-axis by 5% on the right for future data points
            ax1.set_xlim(x_min, x_max + x_range * 0.05)
            ax2.set_xlim(x_min, x_max + x_range * 0.05)
        
        plt.tight_layout()
        return self._plot_to_base64(fig)
    
    def _plot_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        plot_data = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        plot_base64 = base64.b64encode(plot_data).decode('utf-8')
        return f"data:image/png;base64,{plot_base64}"
    
    def _plotly_to_html(self, fig) -> str:
        """Convert Plotly figure to HTML string"""
        return fig.to_html(include_plotlyjs='cdn', config={'responsive': True})
    
    def generate_all_plots(self, y_modes: Dict[str, str] = None) -> Dict[str, str]:
        """Generate all time series plots with specified y-axis scaling for each plot type"""
        plots = {}
        
        # Default y-axis modes for each plot type
        if y_modes is None:
            y_modes = {
                'temperature': 'data_range',
                'humidity': 'data_range', 
                'vpd': 'data_range',
                'foliage': 'data_range'
            }
        
        try:
            df = self.load_recent_data()
            if df is None or df.empty:
                self.logger.warning("No data available for plotting")
                return {}
            
            self.logger.info(f"Generating plots with {len(df)} data points")
            
            # Generate each plot with individual y-axis scaling
            plots['temperature'] = self.create_temperature_plot(df, y_modes.get('temperature', 'data_range'))
            plots['humidity'] = self.create_humidity_plot(df, y_modes.get('humidity', 'data_range'))
            plots['vpd'] = self.create_vpd_plot(df, y_modes.get('vpd', 'data_range'))
            plots['foliage'] = self.create_foliage_plot(df, y_modes.get('foliage', 'data_range'))
            
            self.logger.info("All time series plots generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating plots: {e}")
        
        return plots

if __name__ == "__main__":
    # Test the plotter
    import sys
    import os
    
    # Add the src directory to Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from config import DATA_DIR, CSV_FILE
    
    logging.basicConfig(level=logging.INFO)
    
    csv_path = os.path.join(DATA_DIR, CSV_FILE)
    plotter = TimeSeriesPlotter(csv_path)
    
    plots = plotter.generate_all_plots()
    print(f"Generated {len(plots)} plots")
    for plot_name in plots.keys():
        print(f"- {plot_name}")
