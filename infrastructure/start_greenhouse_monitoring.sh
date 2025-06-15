#!/bin/bash

# Greenhouse Monitoring Background Service
# This script starts all monitoring services and keeps them running
# Can be run in the background or as a service

LOG_DIR="/home/lio/github/greenhouse-monitoring/infrastructure/logs"
SCRIPT_DIR="/home/lio/github/greenhouse-monitoring/infrastructure"
FLOW_FILE="/home/lio/github/greenhouse-monitoring/node-red-flows/greenhouse_integration_complete.json"

# Create logs directory
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/greenhouse_monitor.log"
}

# Function to check if service is running
check_service() {
    local service_name=$1
    if systemctl is-active --quiet $service_name; then
        return 0
    else
        return 1
    fi
}

# Function to check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start InfluxDB
start_influxdb() {
    if check_service influxdb; then
        log "✅ InfluxDB is already running"
    else
        log "🔄 Starting InfluxDB..."
        sudo systemctl start influxdb
        sleep 5
        if check_service influxdb; then
            log "✅ InfluxDB started successfully"
        else
            log "❌ Failed to start InfluxDB"
            exit 1
        fi
    fi
}

# Function to start Grafana
start_grafana() {
    if check_service grafana-server; then
        log "✅ Grafana is already running"
    else
        log "🔄 Starting Grafana..."
        sudo systemctl start grafana-server
        sleep 5
        if check_service grafana-server; then
            log "✅ Grafana started successfully"
        else
            log "❌ Failed to start Grafana"
            exit 1
        fi
    fi
}

# Function to start Node-RED
start_node_red() {
    if check_process "node-red"; then
        log "✅ Node-RED is already running"
    else
        log "🔄 Starting Node-RED..."
        # Kill any zombie Node-RED processes
        pkill -f "node-red" 2>/dev/null
        sleep 2
        
        # Start Node-RED in background
        nohup node-red > "$LOG_DIR/node-red.log" 2>&1 &
        sleep 10
        
        if check_process "node-red"; then
            log "✅ Node-RED started successfully"
        else
            log "❌ Failed to start Node-RED"
            cat "$LOG_DIR/node-red.log"
            exit 1
        fi
    fi
}

# Function to start Telegraf
start_telegraf() {
    if check_process "telegraf"; then
        log "✅ Telegraf is already running"
    else
        log "🔄 Starting Telegraf..."
        # Kill any existing telegraf processes
        pkill -f telegraf 2>/dev/null
        sleep 2
        
        # Export InfluxDB token
        export INFLUX_TOKEN="auGnP6gpNj9iS8I87zVg3HBzR91h1VY13hSkl5ZuWTLy6Q0vnEqhZCrIxBxrg6LibNvjnM1Pxl5Bjt53UpLCww=="
        
        # Start Telegraf with basic config
        nohup telegraf --config "$SCRIPT_DIR/telegraf_basic.toml" > "$LOG_DIR/telegraf.log" 2>&1 &
        sleep 5
        
        if check_process "telegraf"; then
            log "✅ Telegraf started successfully"
        else
            log "❌ Failed to start Telegraf"
            cat "$LOG_DIR/telegraf.log"
            exit 1
        fi
    fi
}

# Function to check ESP32-S3 connectivity
check_esp32() {
    if curl -s --connect-timeout 5 http://192.168.1.176/thermal_data > /dev/null; then
        log "✅ ESP32-S3 thermal camera is accessible at 192.168.1.176"
        return 0
    else
        log "⚠️  ESP32-S3 thermal camera not accessible at 192.168.1.176"
        return 1
    fi
}

# Function to import Node-RED flow
import_node_red_flow() {
    if [ -f "$FLOW_FILE" ]; then
        log "📋 Node-RED flow available: $FLOW_FILE"
        log "   Auto-import will be attempted via API..."
        
        # Wait for Node-RED to be fully ready
        sleep 5
        
        # Try to import flow via Node-RED API
        if curl -s http://localhost:1880 > /dev/null; then
            log "🔗 Node-RED web interface is accessible at http://localhost:1880"
        else
            log "⚠️  Node-RED web interface not yet ready"
        fi
    else
        log "⚠️  Node-RED flow file not found: $FLOW_FILE"
    fi
}

# Function to display status
show_status() {
    log ""
    log "🎯 Greenhouse Monitoring System Status:"
    log "• InfluxDB: $(systemctl is-active influxdb)"
    log "• Grafana: $(systemctl is-active grafana-server)"
    log "• Node-RED: $(check_process "node-red" && echo "active" || echo "inactive")"
    log "• Telegraf: $(check_process "telegraf" && echo "active" || echo "inactive")"
    
    # Check ESP32-S3
    if check_esp32; then
        log "• ESP32-S3: connected (192.168.1.176)"
    else
        log "• ESP32-S3: not connected"
    fi
    
    log ""
    log "🌐 Access URLs:"
    log "• Grafana Dashboard: http://localhost:3000"
    log "• InfluxDB Admin: http://localhost:8086"
    log "• Node-RED Editor: http://localhost:1880"
    log "• ESP32-S3 Thermal: http://192.168.1.176"
    log ""
    log "📊 Credentials:"
    log "• Grafana: admin/admin"
    log "• InfluxDB org: greenhouse"
    log "• InfluxDB bucket: sensors"
    log ""
    log "📁 Log files in: $LOG_DIR/"
}

# Function to monitor services (keep alive)
monitor_services() {
    log "🔄 Starting service monitoring loop..."
    
    while true; do
        # Check and restart services if needed
        if ! check_service influxdb; then
            log "⚠️  InfluxDB stopped, restarting..."
            start_influxdb
        fi
        
        if ! check_service grafana-server; then
            log "⚠️  Grafana stopped, restarting..."
            start_grafana
        fi
        
        if ! check_process "node-red"; then
            log "⚠️  Node-RED stopped, restarting..."
            start_node_red
        fi
        
        if ! check_process "telegraf"; then
            log "⚠️  Telegraf stopped, restarting..."
            start_telegraf
        fi
        
        # Check ESP32-S3 every 5 minutes
        if [ $(($(date +%s) % 300)) -eq 0 ]; then
            check_esp32
        fi
        
        # Sleep for 30 seconds before next check
        sleep 30
    done
}

# Main execution
main() {
    log "🚀 Starting Greenhouse Monitoring System..."
    log "📂 Script directory: $SCRIPT_DIR"
    log "📁 Log directory: $LOG_DIR"
    
    # Start all services
    start_influxdb
    start_grafana
    start_node_red
    start_telegraf
    
    # Import Node-RED flow
    import_node_red_flow
    
    # Check ESP32-S3 connectivity
    check_esp32
    
    # Show status
    show_status
    
    # Start monitoring if requested
    if [[ "$1" == "--monitor" || "$1" == "-m" ]]; then
        log "🔄 Starting continuous monitoring..."
        log "   Press Ctrl+C to stop"
        monitor_services
    else
        log "✅ All services started successfully!"
        log ""
        log "💡 To run with continuous monitoring: $0 --monitor"
        log "💡 To run in background: nohup $0 --monitor > $LOG_DIR/monitor.log 2>&1 &"
    fi
}

# Handle Ctrl+C gracefully
trap 'log "🛑 Stopping greenhouse monitoring..."; exit 0' INT

# Run main function
main "$@"