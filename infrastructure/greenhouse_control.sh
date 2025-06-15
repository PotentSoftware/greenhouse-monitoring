#!/bin/bash

# Greenhouse Monitoring Control Script
# Easy commands to manage your greenhouse monitoring system

SCRIPT_DIR="/home/lio/github/greenhouse-monitoring/infrastructure"
SERVICE_NAME="greenhouse-monitoring"
MAIN_SCRIPT="$SCRIPT_DIR/start_greenhouse_monitoring.sh"

case "$1" in
    start)
        echo "🚀 Starting greenhouse monitoring system..."
        cd "$SCRIPT_DIR"
        bash "$MAIN_SCRIPT"
        ;;
    
    background|bg)
        echo "🚀 Starting greenhouse monitoring in background..."
        cd "$SCRIPT_DIR"
        nohup bash "$MAIN_SCRIPT" --monitor > logs/background.log 2>&1 &
        echo "✅ Started in background (PID: $!)"
        echo "📁 Log file: logs/background.log"
        ;;
    
    monitor)
        echo "🔄 Starting greenhouse monitoring with continuous monitoring..."
        cd "$SCRIPT_DIR"
        bash "$MAIN_SCRIPT" --monitor
        ;;
    
    stop)
        echo "🛑 Stopping greenhouse monitoring processes..."
        pkill -f "start_greenhouse_monitoring.sh"
        pkill -f "node-red"
        pkill -f "telegraf"
        echo "✅ Processes stopped"
        ;;
    
    status)
        echo "🎯 Greenhouse Monitoring System Status:"
        echo "• InfluxDB: $(systemctl is-active influxdb 2>/dev/null || echo 'not installed')"
        echo "• Grafana: $(systemctl is-active grafana-server 2>/dev/null || echo 'not installed')"
        echo "• Node-RED: $(pgrep -f "node-red" > /dev/null && echo "running" || echo "stopped")"
        echo "• Telegraf: $(pgrep -f "telegraf" > /dev/null && echo "running" || echo "stopped")"
        echo "• Monitor Script: $(pgrep -f "start_greenhouse_monitoring.sh" > /dev/null && echo "running" || echo "stopped")"
        
        # Check ESP32-S3
        if curl -s --connect-timeout 3 http://192.168.1.176/thermal_data > /dev/null 2>&1; then
            echo "• ESP32-S3: connected (192.168.1.176)"
        else
            echo "• ESP32-S3: not accessible"
        fi
        
        echo ""
        echo "🌐 Access URLs:"
        echo "• Grafana: http://localhost:3000"
        echo "• Node-RED: http://localhost:1880"
        echo "• InfluxDB: http://localhost:8086"
        echo "• ESP32-S3: http://192.168.1.176"
        ;;
    
    logs)
        echo "📋 Recent greenhouse monitoring logs:"
        if [ -f "$SCRIPT_DIR/logs/greenhouse_monitor.log" ]; then
            tail -n 20 "$SCRIPT_DIR/logs/greenhouse_monitor.log"
        else
            echo "No logs found"
        fi
        ;;
    
    open)
        echo "🌐 Opening monitoring interfaces..."
        if command -v xdg-open > /dev/null; then
            xdg-open http://localhost:3000 2>/dev/null &
            xdg-open http://localhost:1880 2>/dev/null &
            xdg-open http://192.168.1.176 2>/dev/null &
            echo "✅ Opened Grafana, Node-RED, and ESP32-S3 interfaces"
        else
            echo "URLs to open manually:"
            echo "• Grafana: http://localhost:3000"
            echo "• Node-RED: http://localhost:1880"
            echo "• ESP32-S3: http://192.168.1.176"
        fi
        ;;
    
    service-install)
        echo "🔧 Installing systemd service..."
        sudo cp "$SCRIPT_DIR/greenhouse-monitoring.service" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable greenhouse-monitoring
        echo "✅ Service installed and enabled"
        echo "💡 Use 'sudo systemctl start greenhouse-monitoring' to start"
        ;;
    
    service-start)
        echo "🚀 Starting systemd service..."
        sudo systemctl start greenhouse-monitoring
        sudo systemctl status greenhouse-monitoring
        ;;
    
    service-stop)
        echo "🛑 Stopping systemd service..."
        sudo systemctl stop greenhouse-monitoring
        ;;
    
    service-status)
        echo "🎯 Systemd service status:"
        sudo systemctl status greenhouse-monitoring
        ;;
    
    *)
        echo "🌱 Greenhouse Monitoring Control"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Basic Commands:"
        echo "  start         Start monitoring system once"
        echo "  background    Start in background (keeps running)"
        echo "  monitor       Start with continuous monitoring"
        echo "  stop          Stop all monitoring processes"
        echo "  status        Show system status"
        echo "  logs          Show recent logs"
        echo "  open          Open all web interfaces"
        echo ""
        echo "Service Commands (run as background service):"
        echo "  service-install   Install as systemd service"
        echo "  service-start     Start systemd service"
        echo "  service-stop      Stop systemd service"
        echo "  service-status    Check systemd service status"
        echo ""
        echo "Examples:"
        echo "  $0 background     # Start in background"
        echo "  $0 status         # Check what's running"
        echo "  $0 open           # Open all web interfaces"
        echo "  $0 logs           # View recent activity"
        ;;
esac