# Woperator - Web Desktop Streaming Service

## Overview
Woperator is a containerized solution for streaming a virtual desktop environment through a web interface. The project creates a complete virtual desktop environment inside a Docker container and streams both video and audio output to a web browser using FFmpeg for efficient media streaming.

## Features
- Virtual X11 desktop environment running in a container
- Firefox browser running in kiosk mode
- Audio support via PulseAudio
- Real-time desktop streaming using FFmpeg
- Web interface for viewing the stream (port 8000)
- Supervisor-managed processes for reliability

## Prerequisites
- Docker
- Docker Compose
- x86_64 architecture support

## Quick Start
1. Clone the repository:
```bash
git clone https://github.com/yourusername/woperator.git
cd woperator
```

2. Build and run the container:
```bash
docker-compose up --build
```

3. Access the stream:
Open your web browser and navigate to `http://localhost:8000`

## Architecture
The project consists of several key components:

### Container Components
- **Xvfb**: Virtual X11 framebuffer
- **Fluxbox**: Lightweight window manager
- **Firefox**: Web browser in kiosk mode
- **PulseAudio**: Audio server
- **FFmpeg**: Media streaming
- **Python Application**: Web server and stream management

### Process Management
All processes are managed by Supervisor to ensure reliability and proper startup order:
1. Xvfb (Virtual framebuffer)
2. PulseAudio (Audio server)
3. Fluxbox (Window manager)
4. Firefox (Browser instance)
5. Python application (Web server and stream handler)

## Configuration
- Default resolution: 1920x1080
- Streaming port: 8000
- Firefox runs in kiosk mode
- Audio is captured through PulseAudio

## Development
The project structure is organized as follows:
```
woperator/
├── src/
│   ├── app.py
│   └── modules/
├── supervisor/
│   └── supervisord.conf
├── Dockerfile
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
└── README.md
```

## Troubleshooting
1. If the stream doesn't start:
   - Check container logs: `docker-compose logs`
   - Verify all services are running: `docker-compose exec desktop supervisorctl status`

2. Audio issues:
   - Verify PulseAudio is running
   - Check PulseAudio logs in container

## License
MIT License

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
