#!/bin/bash

# Precision Sensors Server Startup Script
# Handles port cleanup and automatic startup

LOG_FILE="/home/debian/precision_server_startup.log"
SERVER_SCRIPT="/home/debian/precision_sensors_server.py"
PORT=8081

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "🚀 Starting Precision Sensors Server startup sequence"

# Check if server script exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    log_message "❌ ERROR: Server script not found at $SERVER_SCRIPT"
    exit 1
fi

# Function to check if port is in use
check_port() {
    netstat -tuln | grep ":$PORT " > /dev/null 2>&1
    return $?
}

# Function to find and kill processes using port 8081
cleanup_port() {
    log_message "🔍 Checking for processes using port $PORT"
    
    # Find processes using port 8081
    PIDS=$(lsof -ti:$PORT 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        log_message "⚠️  Found processes using port $PORT: $PIDS"
        
        # Kill each process
        for PID in $PIDS; do
            PROCESS_INFO=$(ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null)
            if [ -n "$PROCESS_INFO" ]; then
                log_message "🔪 Killing process: $PROCESS_INFO"
                kill -TERM $PID 2>/dev/null
                
                # Wait a moment for graceful shutdown
                sleep 2
                
                # Force kill if still running
                if kill -0 $PID 2>/dev/null; then
                    log_message "💀 Force killing stubborn process $PID"
                    kill -KILL $PID 2>/dev/null
                fi
            fi
        done
        
        # Wait for port to be released
        sleep 3
        
        # Verify port is now free
        if check_port; then
            log_message "❌ ERROR: Port $PORT is still in use after cleanup"
            return 1
        else
            log_message "✅ Port $PORT successfully cleaned up"
        fi
    else
        log_message "✅ Port $PORT is free"
    fi
    
    return 0
}

# Function to kill any existing precision_sensors_server.py processes
cleanup_existing_servers() {
    log_message "🔍 Checking for existing precision_sensors_server.py processes"
    
    EXISTING_PIDS=$(pgrep -f "precision_sensors_server.py" 2>/dev/null)
    
    if [ -n "$EXISTING_PIDS" ]; then
        log_message "⚠️  Found existing server processes: $EXISTING_PIDS"
        
        for PID in $EXISTING_PIDS; do
            PROCESS_INFO=$(ps -p $PID -o pid,ppid,cmd --no-headers 2>/dev/null)
            if [ -n "$PROCESS_INFO" ]; then
                log_message "🔪 Killing existing server: $PROCESS_INFO"
                kill -TERM $PID 2>/dev/null
                
                # Wait for graceful shutdown
                sleep 2
                
                # Force kill if still running
                if kill -0 $PID 2>/dev/null; then
                    log_message "💀 Force killing stubborn server $PID"
                    kill -KILL $PID 2>/dev/null
                fi
            fi
        done
        
        sleep 2
        log_message "✅ Existing server processes cleaned up"
    else
        log_message "✅ No existing server processes found"
    fi
}

# Main startup sequence
log_message "🧹 Starting cleanup sequence"

# Step 1: Clean up existing server processes
cleanup_existing_servers

# Step 2: Clean up port 8081
if ! cleanup_port; then
    log_message "❌ FATAL: Could not clean up port $PORT"
    exit 1
fi

# Step 3: Wait a moment for system to stabilize
log_message "⏳ Waiting for system to stabilize..."
sleep 3

# Step 4: Start the precision sensors server
log_message "🌱 Starting Precision Sensors Server"

cd /home/debian

# Start server in background with output redirection
python3 "$SERVER_SCRIPT" > precision_server.log 2>&1 &
SERVER_PID=$!

# Wait a moment to check if server started successfully
sleep 5

# Verify server is running
if kill -0 $SERVER_PID 2>/dev/null; then
    log_message "✅ Precision Sensors Server started successfully (PID: $SERVER_PID)"
    
    # Verify port is now in use by our server
    if check_port; then
        log_message "✅ Server is listening on port $PORT"
        log_message "🎉 Startup sequence completed successfully"
        exit 0
    else
        log_message "⚠️  WARNING: Server started but port $PORT not detected as in use"
        exit 0
    fi
else
    log_message "❌ FATAL: Server failed to start"
    
    # Show last few lines of server log for debugging
    if [ -f "/home/debian/precision_server.log" ]; then
        log_message "📋 Last server log entries:"
        tail -10 /home/debian/precision_server.log | while read line; do
            log_message "   $line"
        done
    fi
    
    exit 1
fi
