#!/bin/bash
echo "Setting up InfluxDB..."
influx setup \
  --username admin \
  --password greenhouse123 \
  --org greenhouse \
  --bucket sensors \
  --retention 30d \
  --force
echo "InfluxDB setup complete!"
echo "Access InfluxDB at: http://localhost:8086"
echo "Username: admin"
echo "Password: greenhouse123"
