FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add Mozilla PPA for Firefox ESR
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:mozillateam/ppa

# Install system dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    xvfb \
    x11vnc \
    xterm \
    fluxbox \
    novnc \
    websockify \
    supervisor \
    pulseaudio \
    ffmpeg \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxrandr2 \
    libasound2t64 \
    libpulse0 \
    libopus0 \
    libvpx9 \
    portaudio19-dev \
    gnome-screenshot \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-tk \
    python3-xlib \
    xauth \
    x11-xserver-utils \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash app_user && \
    mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix

# Set up working directory and change ownership
WORKDIR /app
RUN chown -R app_user:app_user /app

# Create and activate virtual environment
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install wheel first
RUN pip install --no-cache-dir wheel setuptools

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .
RUN chown -R app_user:app_user /app

# Set up PulseAudio configuration
RUN mkdir -p /home/app_user/.config/pulse && \
    chown -R app_user:app_user /home/app_user/.config

# Expose port
EXPOSE 8000

# Set up entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh && \
    chown app_user:app_user /docker-entrypoint.sh

# Switch to non-root user
USER app_user

ENTRYPOINT ["/docker-entrypoint.sh"] 