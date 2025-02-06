#!/bin/bash

# Function to wait for port to be free
wait_for_port() {
    local port=$1
    while lsof -i :$port >/dev/null 2>&1; do
        echo "Waiting for port $port to be free..."
        sleep 1
    done
}

# Cleanup any existing X server locks
rm -f /tmp/.X1-lock
rm -f /tmp/.X11-unix/X1

# Start virtual display
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1

# Wait for X server to start and create socket
for i in $(seq 1 10); do
    if [ -e "/tmp/.X11-unix/X1" ]; then
        break
    fi
    echo "Waiting for X socket to be created... ($i/10)"
    sleep 1
done

if [ ! -e "/tmp/.X11-unix/X1" ]; then
    echo "Failed to start X server"
    exit 1
fi

# Set proper permissions for the X socket
chmod 1777 /tmp/.X11-unix
chmod a+w /tmp/.X11-unix/X1

# Start window manager
fluxbox &

# Wait for window manager to start
sleep 3

# Start Firefox in the background
firefox-esr --no-remote --new-instance "http://localhost:8000" &

# Configure PulseAudio
export PULSE_SERVER=unix:/tmp/pulseaudio.socket
pulseaudio --start --disallow-exit --exit-idle-time=-1 \
    --load="module-native-protocol-unix auth-anonymous=1 socket=/tmp/pulseaudio.socket" \
    --load="module-native-protocol-tcp auth-ip-acl=127.0.0.1 auth-anonymous=1" &

# Wait for PulseAudio to start
sleep 2

# Wait for backend port to be available
wait_for_port 8000

# Start the Python application
cd /app && /app/venv/bin/python /app/src/app.py 