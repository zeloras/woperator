#!/bin/bash

# Set up X11 authentication
rm -rf /root/.Xauthority
touch /root/.Xauthority

# Remove any existing X locks
rm -f /tmp/.X0-lock

# Start PulseAudio
pulseaudio --start --exit-idle-time=-1

# Start Xvfb
Xvfb :0 -screen 0 1920x1080x24 &

# Wait for X server to start
sleep 1

# Set up X11 authentication
xauth generate :0 . trusted

# Start Fluxbox window manager
fluxbox &

# Start Firefox with specific settings
firefox-esr --no-remote --new-instance "http://localhost:8000" &

# Start the Python application
/opt/venv/bin/python3 /app/src/app.py 