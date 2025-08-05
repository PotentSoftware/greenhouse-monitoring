#!/usr/bin/env python3
"""
Cleanup script to identify and remove redundant tCam-Mini files
"""

import os
import shutil
from pathlib import Path

def cleanup_redundant_files():
    """Remove redundant and obsolete files"""
    
    scripts_dir = Path("/home/lio/github/greenhouse-monitoring/tcam-mini-integration/scripts")
    
    # Files to remove (redundant or obsolete)
    redundant_files = [
        # Obsolete test files (functionality now in main tools)
        "simple_tcam_test.py",
        "tcam_basic_test.py", 
        "tcam_command_test.py",
        "tcam_socket_test.py",
        "test_tcam_connection.py",
        "quick_tcam_test.py",
        "scan_for_tcam.py",
        
        # Redundant connection/diagnostic tools
        "diagnose_tcam_connection.py",
        "find_tcam_client.py",
        "find_tcam_device.py",
        
        # Obsolete AP mode tools (now using station mode)
        "tcam_ap_capture.py",
        "tcam_ap_mode_test.py",
        "configure_client_mode.py",
        "switch_wifi.sh",
        "connect_tcam_robust.sh",
        "connect_tcam_simple.sh",
        "setup_client_mode_workflow.sh",
        
        # Redundant capture tools (superseded by GUI)
        "tcam_image_capture.py",
        "enhanced_thermal_viewer.py",
        "tcam_thermal_viewer.py",
        
        # Redundant analysis tools
        "analyze_captures.py",
        "test_temperature_conversion.py",
        "test_station_mode.py",
    ]
    
    removed_files = []
    kept_files = []
    
    print("🧹 Cleaning up redundant tCam-Mini files...")
    print("=" * 50)
    
    for filename in redundant_files:
        file_path = scripts_dir / filename
        if file_path.exists():
            print(f"🗑️  Removing: {filename}")
            file_path.unlink()
            removed_files.append(filename)
        else:
            print(f"⚠️  Not found: {filename}")
    
    # List essential files to keep
    essential_files = [
        # Primary user tools
        "thermal_capture_gui.py",           # Main GUI tool
        "debug_tcam_commands.py",           # Command testing
        "wireless_connectivity_test.py",   # Wireless testing
        "quick_thermal_view.py",           # Single image capture
        
        # Network tools
        "find_tcam_on_network.py",         # Network scanning
        "tcam_network_diagnostic.py",      # Diagnostics
        
        # Web interface
        "tcam_web_interface.py",           # Web interface
        "thermal_web_simple.py",           # Simple web interface
        
        # Advanced tools
        "live_thermal_viewer.py",          # Live viewing
        "multi_format_thermal_capture.py", # Batch capture
        "raw_thermal_viewer.py",           # Raw data viewer
        
        # Protocol and testing
        "correct_protocol_test.py",        # Protocol validation
        "simple_socket_test.py",           # Basic socket test
        "test_socket_commands.py",         # Socket command test
        "test_tcam_station_mode.py",       # Station mode test
        "test_thermal_image.py",           # Thermal image test
        "test_wireless.py",                # Wireless test
        
        # Analysis tools
        "analyze_thermal_file.py",         # File analysis
        "leaf_detection_prototype.py",     # ML prototype
    ]
    
    print(f"\n✅ Removed {len(removed_files)} redundant files")
    print(f"📁 Keeping {len(essential_files)} essential files")
    
    # Verify essential files exist
    print("\n📋 Essential files status:")
    for filename in essential_files:
        file_path = scripts_dir / filename
        if file_path.exists():
            kept_files.append(filename)
            print(f"✅ {filename}")
        else:
            print(f"❌ Missing: {filename}")
    
    return removed_files, kept_files

if __name__ == "__main__":
    removed, kept = cleanup_redundant_files()
    print(f"\n🎯 Cleanup complete: {len(removed)} removed, {len(kept)} kept")
