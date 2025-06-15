#!/bin/bash

echo "🔧 Starting Telegraf for Greenhouse Monitoring..."

# Set the InfluxDB token environment variable
export INFLUX_TOKEN="auGnP6gpNj9iS8I87zVg3HBzR91h1VY13hSkl5ZuWTLy6Q0vnEqhZCrIxBxrg6LibNvjnM1Pxl5Bjt53UpLCww=="

# Run Telegraf with our custom config
telegraf --config /home/lio/github/integration/infrastructure/telegraf_config.toml

echo "Telegraf stopped."
