# Явно указываем платформу x86_64
FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Add Mozilla PPA for Firefox ESR
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:mozillateam/ppa

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    fluxbox \
    firefox-esr \
    python3-full \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

COPY requirements.txt .

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Set up entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENV DISPLAY=:0

ENTRYPOINT ["/docker-entrypoint.sh"]