# tCam-Mini Integration - File Index

## 📁 Essential Files Overview

### 🎯 **Primary User Tools**
| File | Purpose | Usage |
|------|---------|-------|
| `thermal_capture_gui.py` | **Main GUI tool** | One-click 10-image capture in all formats |
| `debug_tcam_commands.py` | Command testing | Test all tCam API commands |
| `wireless_connectivity_test.py` | Wireless validation | Comprehensive connectivity testing |
| `quick_thermal_view.py` | Single image capture | Quick thermal image capture and display |

### 🌐 **Network & Diagnostics**
| File | Purpose | Usage |
|------|---------|-------|
| `find_tcam_on_network.py` | Network scanning | Find tCam-Mini IP address on network |
| `tcam_network_diagnostic.py` | Troubleshooting | Comprehensive network diagnostics |

### 🖥️ **Web Interfaces**
| File | Purpose | Usage |
|------|---------|-------|
| `tcam_web_interface.py` | Full web interface | Browser-based thermal viewing |
| `thermal_web_simple.py` | Simple web interface | Lightweight web viewer |

### 📊 **Advanced Tools**
| File | Purpose | Usage |
|------|---------|-------|
| `live_thermal_viewer.py` | Live viewing | Real-time thermal image display |
| `multi_format_thermal_capture.py` | Batch capture | Command-line multi-format capture |
| `raw_thermal_viewer.py` | Raw data viewer | View and analyze raw thermal data |
| `analyze_thermal_file.py` | File analysis | Analyze captured thermal files |

### 🧪 **Testing & Validation**
| File | Purpose | Usage |
|------|---------|-------|
| `correct_protocol_test.py` | Protocol validation | Verify tCam communication protocol |
| `simple_socket_test.py` | Basic connectivity | Simple socket connection test |
| `test_socket_commands.py` | Command testing | Test individual socket commands |
| `test_tcam_station_mode.py` | Station mode test | Verify wireless station mode |
| `test_thermal_image.py` | Image capture test | Test thermal image capture |
| `test_wireless.py` | Wireless test | Test wireless functionality |

### 🤖 **Machine Learning**
| File | Purpose | Usage |
|------|---------|-------|
| `leaf_detection_prototype.py` | Plant analysis | ML-based leaf detection and analysis |

## 🔧 **Firmware & Configuration**
| Directory/File | Purpose |
|----------------|---------|
| `firmware/` | Station mode firmware and flashing tools |
| `firmware/flash_station_mode.sh` | Flash station mode configuration |
| `firmware/station_mode_config/` | Custom WiFi configuration firmware |

## 📚 **Documentation**
| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `WIRELESS_DEPLOYMENT_SUCCESS.md` | **Complete deployment guide** |
| `NETWORK_SOLUTION_GUIDE.md` | Network configuration guide |
| `CLEANUP_SUMMARY.md` | File cleanup summary |
| `FILE_INDEX.md` | This file index |

## 🚀 **Quick Start Guide**

### **For New Users:**
1. **Start here**: `README.md`
2. **Main tool**: `python3 thermal_capture_gui.py`
3. **If issues**: `python3 tcam_network_diagnostic.py`

### **For Developers:**
1. **Protocol testing**: `python3 debug_tcam_commands.py`
2. **Network discovery**: `python3 find_tcam_on_network.py`
3. **Web interface**: `python3 tcam_web_interface.py`

### **For Analysis:**
1. **File analysis**: `python3 analyze_thermal_file.py`
2. **ML processing**: `python3 leaf_detection_prototype.py`
3. **Raw data**: `python3 raw_thermal_viewer.py`

## 🗑️ **Recently Removed (Redundant)**
- 23 obsolete test files and duplicate tools
- AP mode tools (now using station mode)
- Redundant capture and analysis scripts
- Old connection and diagnostic tools

## 📊 **File Statistics**
- **Total Essential Files**: 19 Python scripts
- **Documentation Files**: 5 markdown files
- **Firmware Files**: Complete station mode package
- **Removed Redundant**: 23 obsolete files
- **Net Cleanup**: Streamlined from 42 to 19 core scripts

---
*Last updated: 2025-08-05 - Post wireless deployment success*
