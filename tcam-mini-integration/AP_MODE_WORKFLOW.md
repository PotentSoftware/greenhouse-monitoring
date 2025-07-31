# tCam-Mini AP Mode Development Workflow

## Quick Start Guide

### 1. Switch to tCam-Mini Network
```bash
cd /home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts
./switch_wifi.sh tcam
```

### 2. Capture Data (While Connected to tCam)
```bash
python3 tcam_ap_capture.py
```
This will:
- Test all API endpoints
- Capture thermal data
- Save multiple frames
- Store everything for offline analysis

### 3. Switch Back to Home Network
```bash
./switch_wifi.sh home
```

### 4. Analyze Captured Data
```bash
python3 analyze_captures.py
```
This will:
- Analyze thermal statistics
- Create visualizations
- Generate leaf detection previews
- Show API endpoint information

## File Locations

- **Captures**: `/home/lio/github/greenhouse-monitoring/tcam-mini-integration/captures/`
- **Scripts**: `/home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts/`
- **Each session**: `captures/session_YYYYMMDD_HHMMSS/`

## Session Contents

Each capture session creates:
- `capture_summary.json` - Overview of all API responses
- `thermal_pixels.json` - Raw thermal pixel data
- `thermal_frames.json` - Multiple thermal captures
- `thermal_analysis.png` - Visualization and analysis
- Any images captured from API endpoints

## Tips

1. **Quick Testing**: The capture script runs in ~30 seconds
2. **Multiple Sessions**: Each run creates a new timestamped session
3. **Specific Analysis**: Run `python3 analyze_captures.py /path/to/session` to analyze a specific session
4. **Network Status**: Use `./switch_wifi.sh status` to check current connection

## Next Steps

After capturing and analyzing data:
1. Review thermal images for leaf patterns
2. Check API responses for configuration options
3. Plan leaf detection algorithm based on thermal patterns
4. Consider firmware modifications for production use
