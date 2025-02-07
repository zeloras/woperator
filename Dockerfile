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
    python3-dev \
    python3-setuptools \
    xdotool \
    dbus-x11 \
    pulseaudio \
    ffmpeg \
    x11-utils \
    libavdevice-dev \
    libavfilter-dev \
    libopus-dev \
    libvpx-dev \
    libx264-dev \
    libsrtp2-dev \
    python3-opencv \
    libxcb-randr0-dev \
    libxcb-xfixes0-dev \
    libxrender-dev \
    libva-dev \
    vainfo \
    mesa-utils \
    libgl1-mesa-dri \
    libpulse-dev \
    libasound2-dev \
    libglx0 \
    libgl1 \
    libgl1-mesa-dev \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Configure PulseAudio
RUN mkdir -p /etc/pulse && \
    echo "load-module module-native-protocol-unix auth-anonymous=1" > /etc/pulse/system.pa && \
    echo "load-module module-native-protocol-tcp auth-anonymous=1" >> /etc/pulse/system.pa && \
    echo "load-module module-always-sink" >> /etc/pulse/system.pa && \
    echo "load-module module-null-sink sink_name=virtual_sink sink_properties=device.description=Virtual_Output" >> /etc/pulse/system.pa && \
    echo "load-module module-null-sink sink_name=virtual_monitor sink_properties=device.description=Monitor_Output" >> /etc/pulse/system.pa && \
    echo "load-module module-loopback source=virtual_sink.monitor sink=virtual_monitor" >> /etc/pulse/system.pa && \
    echo "set-default-sink virtual_sink" >> /etc/pulse/system.pa && \
    echo "set-default-source virtual_sink.monitor" >> /etc/pulse/system.pa

WORKDIR /app

COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENV DISPLAY=:99
ENV PULSE_SERVER=/var/run/pulse/native
ENV XDG_RUNTIME_DIR=/tmp

RUN mkdir -p /var/log/supervisor && chown -R root:root /var/log/supervisor

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]