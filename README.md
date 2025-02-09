# Woperator

A lightweight VNC-like remote desktop solution built with Python and websockify.

## Architecture

```
├── src/                    # Source code
│   ├── server/            # Server-side implementation
│   │   ├── vnc.py        # VNC server implementation
│   │   ├── audio.py      # Audio capture and streaming
│   │   └── websock.py    # Websocket server
│   ├── web/              # Web interface
│   │   ├── static/       # Static files (JS, CSS)
│   │   └── templates/    # HTML templates
│   └── utils/            # Utility functions
├── docker/               # Docker related files
│   └── Dockerfile       # Main Dockerfile
├── tests/               # Test files
├── docker-compose.yml   # Docker Compose configuration
└── requirements.txt     # Python dependencies
```

## Features

- Screen sharing from Docker container
- Audio capture and streaming
- Remote control capabilities
- Custom web interface
- Based on Ubuntu 22.04 with Python 3.12

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/woperator.git
cd woperator
```

2. Start the container:
```bash
docker-compose up -d
```

3. Access the web interface at `http://localhost:6080`

## Development

### Setup Development Environment

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Building Docker Image

```bash
docker build -t woperator -f docker/Dockerfile .
```

## Configuration

The application can be configured through environment variables:

- `VNC_PORT`: VNC server port (default: 5900)
- `WEB_PORT`: Web interface port (default: 6080)
- `DISPLAY`: Display number (default: :0)

## License

MIT License
