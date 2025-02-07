import os
import pathlib

# Пути
BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'

# Настройки сервера
HOST = '0.0.0.0'
PORT = 8000

# Настройки X11
DISPLAY = ':99'

# Настройки FFmpeg
FFMPEG_VIDEO_SETTINGS = {
    'framerate': 30,
    'video_size': '1280x720',
    'quality': 5,
    'threads': 8
}

FFMPEG_AUDIO_SETTINGS = {
    'bitrate': '128k',
    'sample_rate': 44100,
    'channels': 2
}

# Настройки логирования
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Настройки WebSocket
WS_CHUNK_SIZE = 16384
AUDIO_CHUNK_SIZE = 8192

# Директории для проверки
REQUIRED_DIRS = {
    '/app': 0o755,
    '/app/stream': 0o755
} 