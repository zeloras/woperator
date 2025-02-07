# Woperator - Web Desktop Streaming Service

## Overview
Woperator is a containerized solution for streaming a virtual desktop environment through a web interface using WebRTC for ultra-low latency communication. The project creates a complete virtual desktop environment inside a Docker container and streams both video/audio output via WebRTC protocol.

## Features
- Virtual X11 desktop environment running in a container
- WebRTC-based streaming с минимальной задержкой
- STUN/TURN сервер для NAT-трансверсали
- Адаптивное качество потока (Simulcast)
- Firefox browser running in kiosk mode
- Web interface with WebRTC client (port 8000)

## Prerequisites
- Docker
- Docker Compose
- x86_64 architecture support

## Quick Start
1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/woperator.git
cd woperator
```

2. Запустите сервисы (основной контейнер + Janus Gateway):
```bash
docker-compose -f docker-compose.yml -f janus/docker-compose.janus.yml up --build
```

3. Откройте веб-интерфейс:
`http://localhost:8000`

## Architecture
### Key Components
- **Janus Gateway**: WebRTC медиасервер
- **GStreamer**: Захват и обработка медиапотока
- **Xvfb**: Virtual framebuffer
- **Fluxbox**: Window manager
- **WebRTC Client**: Веб-интерфейс для просмотра

### Data Flow
1. Захват экрана через Xvfb
2. Кодирование потока через GStreamer
3. Трансляция через Janus Gateway
4. Клиентское подключение по WebRTC

## Configuration
```ini
# WebRTC параметры
STUN_SERVER=stun:stun.l.google.com:19302
TURN_SERVER=turn:your.turn.server:5349
SIMULCAST=true
RESOLUTION=1920x1080@30fps
```

## Development Changes
```
woperator/
├── janus/               # Конфиги Janus Gateway
├── webrtc/              # WebRTC клиент
└── src/
    └── stream_handler.py # GStreamer pipeline management
```

## Troubleshooting
1. Проблемы с подключением:
   - Проверьте доступность портов 8088(Janus) и 8000(Web)
   - Убедитесь в работе STUN/TURN серверов
   
2. Проблемы с потоком:
```bash
docker-compose logs gstreamer
docker-compose logs janus
```

## License
MIT License

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
