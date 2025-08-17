# Jetson Orin Nano - Interactive Thermal Viewer Features

## Overview
The Jetson Orin Nano greenhouse monitoring system now includes a fully interactive thermal image viewer with real-time pixel temperature analysis and recording capabilities.

## New Features Added

### 1. Interactive Pixel Temperature Display
- **Mouse Hover**: Real-time display of pixel coordinates and temperature as you move the mouse over the thermal image
- **Live Feedback**: Shows `Mouse: X=80, Y=60, Temp=24.5°C` in a dedicated display area
- **Crosshair Cursor**: Visual indicator that the image is interactive

### 2. Click-to-Record Pixel Values
- **Left-Click Recording**: Click anywhere on the thermal image to record that pixel's coordinates and temperature
- **Timestamp Tracking**: Each recorded pixel includes the time it was captured
- **Persistent Storage**: Recorded pixels remain visible across image refreshes

### 3. Recorded Pixels Widget
- **Organized Display**: Shows all recorded pixels in a dedicated panel below the thermal image
- **Detailed Information**: Each entry shows:
  - Pixel number (Pixel 1, Pixel 2, etc.)
  - X,Y coordinates
  - Original temperature and current temperature (if changed)
  - Recording timestamp
- **Temperature Tracking**: Shows temperature changes as `24.5°C -> 25.1°C` when new images are captured

### 4. Temperature Change Tracking
- **Persistent Monitoring**: Recorded pixels automatically update with new temperature values from fresh thermal images
- **Change Visualization**: Clear indication when pixel temperatures change between image captures
- **Historical Reference**: Original recorded temperature is preserved alongside current values

### 5. Clear Functionality
- **Reset Button**: "Clear All" button to remove all recorded pixel values
- **Fresh Start**: Allows users to start new measurement sessions

## Technical Implementation

### New API Endpoints
- `/api/thermal_pixel_data` - Serves thermal data as JSON for pixel interactions
- Enhanced `/thermal_viewer` - Interactive thermal image viewer page
- Enhanced `/thermal_image.png` - Real thermal camera data (160x120 pixels)
- `/thermal_data.npy` - Downloadable numpy array format

### Data Flow
1. **Image Display**: Real thermal camera data from tCam-Mini (160x120 resolution)
2. **Pixel Lookup**: JavaScript fetches thermal data array for temperature calculations
3. **Coordinate Mapping**: Mouse coordinates are scaled to thermal image pixel coordinates
4. **Temperature Retrieval**: Direct lookup from thermal data array for accurate readings
5. **Persistent Tracking**: Recorded pixels update automatically with new thermal data

### Browser Compatibility
- **Modern Browsers**: Uses ES6 features (template literals, arrow functions)
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Auto-refresh every 5 seconds with smooth transitions

## User Interface Enhancements

### Visual Design
- **Dark Theme**: Professional dark interface matching the main dashboard
- **Green Accents**: Jetson Orin Nano branding colors (#76b900)
- **Clear Typography**: Easy-to-read temperature values and coordinates
- **Smooth Transitions**: No flickering during image updates

### Navigation
- **New Tab Opening**: Tools → Thermal Image opens in a new browser tab
- **Navigation Buttons**: Easy access to dashboard, raw data, and .npy downloads
- **Refresh Controls**: Manual refresh button and auto-refresh toggle

## Usage Instructions

### Basic Operation
1. Access the thermal viewer via **Tools → Thermal Image** from the main dashboard
2. Move mouse over the thermal image to see live pixel temperatures
3. Click anywhere to record that pixel's temperature and coordinates
4. Watch recorded pixels update automatically as new images are captured
5. Use "Clear All" to reset recorded values

### Advanced Features
- **Download Raw Data**: Use "Download .npy" button for scientific analysis
- **Temperature Monitoring**: Track specific plant areas or equipment over time
- **Comparative Analysis**: Record multiple points to compare temperatures across the greenhouse

## Technical Specifications

### Image Resolution
- **Thermal Camera**: 160x120 pixels (tCam-Mini)
- **Temperature Range**: Typically 20-30°C for greenhouse monitoring
- **Precision**: 0.1°C resolution from FLIR Lepton sensor
- **Update Rate**: 5-second auto-refresh

### Data Format
- **Display Format**: Celsius with 1 decimal place (24.5°C)
- **Coordinate System**: X=0-159, Y=0-119 (top-left origin)
- **Raw Data**: Available as .npy format for external analysis
- **JSON API**: Real-time access to thermal data array

## Troubleshooting

### Common Issues
- **No Image Display**: Check tCam-Mini connection (192.168.1.130:5001)
- **Pixel Values Not Updating**: Verify thermal camera data is being received
- **Mouse Coordinates Off**: Ensure browser zoom is at 100%
- **Strange Characters**: Fixed in latest version using simple text arrows

### Performance
- **Memory Usage**: Optimized image preloading prevents flickering
- **Network Traffic**: Efficient JSON data transfer for pixel interactions
- **Browser Performance**: Smooth operation on modern browsers

## Future Enhancements

### Planned Features
- **Temperature Alerts**: Notifications when recorded pixels exceed thresholds
- **Data Export**: CSV export of recorded pixel temperature history
- **Heat Maps**: Overlay visualization of temperature zones
- **Time Series**: Historical temperature tracking for recorded pixels

### Integration Possibilities
- **Plant Monitoring**: Track leaf temperatures for stress detection
- **Equipment Monitoring**: Monitor heating/cooling system performance
- **Environmental Analysis**: Correlate thermal data with humidity and VPD measurements

## Version History

### v1.1.0 (August 2025)
- ✅ Interactive pixel temperature display
- ✅ Click-to-record functionality
- ✅ Recorded pixels widget with temperature tracking
- ✅ Smooth image refresh without flickering
- ✅ Character encoding fixes
- ✅ Real thermal camera data integration
- ✅ .npy download capability

### v1.0.0 (Previous)
- Basic thermal image display
- Static temperature statistics
- Manual refresh only
