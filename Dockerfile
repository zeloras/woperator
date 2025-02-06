# Явно указываем платформу x86_64
FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add Mozilla PPA for Firefox
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:mozillateam/ppa && \
    echo 'Package: *' > /etc/apt/preferences.d/mozilla-firefox && \
    echo 'Pin: release o=LP-PPA-mozillateam' >> /etc/apt/preferences.d/mozilla-firefox && \
    echo 'Pin-Priority: 1001' >> /etc/apt/preferences.d/mozilla-firefox

# Install system dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    xvfb \
    fluxbox \
    firefox \
    python3-full \
    python3-pip \
    xdotool \
    dbus-x11 \
    pulseaudio \
    ffmpeg \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Configure PulseAudio
RUN mkdir -p /etc/pulse && \
    echo "default-server = unix:/var/run/pulse/native" > /etc/pulse/client.conf && \
    echo "autospawn = no" >> /etc/pulse/client.conf && \
    echo "daemon-binary = /bin/true" >> /etc/pulse/client.conf && \
    echo "enable-shm = yes" >> /etc/pulse/client.conf && \
    echo "load-module module-native-protocol-unix auth-anonymous=1" > /etc/pulse/system.pa && \
    echo "load-module module-native-protocol-tcp auth-anonymous=1" >> /etc/pulse/system.pa && \
    echo "load-module module-always-sink" >> /etc/pulse/system.pa && \
    echo "load-module module-null-sink" >> /etc/pulse/system.pa && \
    echo "load-module module-x11-publish" >> /etc/pulse/system.pa

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENV DISPLAY=:99
ENV PULSE_SERVER=unix:/var/run/pulse/native
ENV XDG_RUNTIME_DIR=/tmp

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]