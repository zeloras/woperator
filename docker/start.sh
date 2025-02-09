#!/bin/bash

# Disable IPv6
sysctl -w net.ipv6.conf.all.disable_ipv6=1
sysctl -w net.ipv6.conf.default.disable_ipv6=1

# Kill any existing processes
pkill -9 pulseaudio
pkill -9 Xvfb
pkill -9 x11vnc
pkill -9 websockify
pkill -9 python3

# Clean up any existing files
rm -rf /tmp/.X*
rm -rf /tmp/pulseaudio*

# Create necessary directories with proper permissions
mkdir -p /tmp/pulseaudio
chmod -R 777 /tmp/pulseaudio

# Wait for ports to be available
wait_for_port() {
    for i in {1..30}; do
        if ! nc -z localhost $1; then
            return 0
        fi
        echo "Waiting for port $1 to be available..."
        sleep 1
    done
    return 1
}

wait_for_port 5900
wait_for_port 6080

# Start Xvfb
Xvfb :0 -screen 0 1920x1080x24 &
export DISPLAY=:0

# Configure and start PulseAudio with null sink
pulseaudio --system --disallow-exit --disallow-module-loading --exit-idle-time=-1 \
    --load="module-null-sink sink_name=DummyOutput sink_properties=device.description=DummyOutput" \
    --load="module-native-protocol-unix auth-anonymous=1 socket=/tmp/pulseaudio.socket" \
    --daemonize

# Start VNC server with optimized settings for macOS
x11vnc -display :0 -nopw -forever -shared -noxdamage -noipv6 &

# Start window manager
fluxbox &

# Start the Python application
cd /app && python3 src/server/websock.py 