FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add repositories and install basic tools
RUN apt-get update && apt-get install -y software-properties-common wget gnupg2
RUN add-apt-repository ppa:deadsnakes/ppa

# Add Google Chrome repository
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y \
    curl \
    x11vnc \
    xvfb \
    fluxbox \
    wget \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-distutils \
    python3-pip \
    python3.12-full \
    build-essential \
    portaudio19-dev \
    pulseaudio \
    pulseaudio-utils \
    netstat-nat \
    lsof \
    net-tools \
    google-chrome-stable \
    tigervnc-standalone-server \
    tigervnc-common \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Configure PulseAudio
RUN mkdir -p /var/run/pulse /var/lib/pulse /root/.config/pulse
RUN adduser root pulse-access
RUN chmod -R 777 /var/run/pulse /var/lib/pulse /root/.config/pulse

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pip and basic tools in virtual environment
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir --ignore-installed -r requirements.txt

# Copy application code
COPY . .

# Set up VNC password
RUN mkdir -p ~/.vnc && x11vnc -storepasswd "vncpass" ~/.vnc/passwd

# Set up virtual display
ENV DISPLAY=:0

# Add Chrome to startup
RUN mkdir -p ~/.fluxbox && echo "google-chrome --no-sandbox --start-maximized &" >> ~/.fluxbox/startup

# Expose ports
EXPOSE 5900 6080

# Start script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"] 