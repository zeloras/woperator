# Woperator - Web Desktop Streaming Service

## Overview
Woperator is a containerized solution for streaming a virtual desktop environment through a web interface. The project creates a complete virtual desktop environment inside a Docker container and streams both video and audio output via WebSocket protocol, providing a low-latency interactive experience.

## Features
- Virtual X11 desktop environment running in a container
- Low-latency WebSocket-based streaming
- Interactive mode for mouse control
- Audio streaming support
- Modern web interface with chat functionality
- Firefox browser running in kiosk mode

## Architecture
### Components
- **Frontend**:
  - Modern responsive web interface
  - WebSocket client for real-time communication
  - Interactive controls and chat system
  - Audio/Video stream handling

- **Backend**:
  - aiohttp WebSocket server
  - FFmpeg for screen and audio capture
  - X11 environment with Xvfb
  - PulseAudio for audio handling

### Project Structure
```
src/
├── __init__.py
├── app.py                # Main application server
├── config.py            # Configuration settings
├── ffmpeg_stream.py     # FFmpeg streaming functionality
├── logger.py            # Logging configuration
├── websocket_handler.py # WebSocket communication
├── x11_utils.py         # X11 utilities
├── static/             # Static assets
│   ├── css/
│   │   └── style.css   # Application styles
│   └── js/
│       └── app.js      # Frontend JavaScript
└── templates/          # HTML templates
    └── index.html      # Main application template
```

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

2. Start the service:
```bash
docker-compose up --build
```

3. Access the web interface:
```
http://localhost:8000
```

## Features in Detail

### Interactive Mode
- Click the "Interactive Mode" button to enable mouse control
- Mouse movements and clicks are transmitted to the virtual desktop
- Real-time cursor position display

### Audio Control
- Toggle audio streaming with the "Enable Audio" button
- Automatic audio initialization and buffering
- Support for system audio capture

### Chat System
- Real-time chat functionality
- Persistent chat history during session
- Clean and intuitive interface
- Support for future extensibility

### Settings (Coming Soon)
- Placeholder for future settings implementation
- Modular design for easy feature addition

## Technical Details

### Streaming Protocol
- WebSocket-based communication
- Binary frame transmission for video
- MP3-encoded audio streaming
- JSON-based control messages

### Video Streaming
- FFmpeg x11grab for screen capture
- MJPEG encoding for low latency
- Configurable quality and frame rate
- Efficient frame buffering

### Audio Streaming
- PulseAudio virtual sink
- MP3 encoding for compatibility
- Configurable audio quality
- Buffer management for smooth playback

### Container Configuration
- Ubuntu-based image
- Xvfb virtual framebuffer
- Fluxbox window manager
- Supervisor process management

## Configuration
Key settings in `src/config.py`:
```python
# Server settings
HOST = '0.0.0.0'
PORT = 8000

# Video settings
FFMPEG_VIDEO_SETTINGS = {
    'framerate': 60,
    'video_size': '1920x1080',
    'quality': 3,
    'threads': 4
}

# Audio settings
FFMPEG_AUDIO_SETTINGS = {
    'bitrate': '128k',
    'sample_rate': 44100,
    'channels': 2
}
```

## Development
1. Code Style
   - Follow PEP 8 guidelines
   - Use type hints where applicable
   - Maintain modular structure

2. Adding Features
   - Create new modules in `src/`
   - Update configuration in `config.py`
   - Add frontend components in `static/`

3. Testing
   - Test WebSocket connectivity
   - Verify audio/video sync
   - Check browser compatibility

## Troubleshooting
1. Connection Issues
   - Verify port 8000 is available
   - Check WebSocket connection status
   - Review server logs

2. Stream Problems
   - Check FFmpeg process status
   - Verify X11 configuration
   - Monitor resource usage

## License
MIT License

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
