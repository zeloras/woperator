#!/bin/bash

# Remove any existing X locks
rm -f /tmp/.X0-lock

# Start Xvfb
Xvfb :0 -screen 0 1920x1080x24 &

# Wait for X server to start
sleep 1

# Start Fluxbox window manager
fluxbox &

# Start Firefox browser
firefox-esr &

# Start the Python application
python3 /app/src/app.py 