import os
from typing import Dict, Any
import logging
from dotenv import load_dotenv

class Config:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from environment variables and defaults"""
        load_dotenv()

        self.config: Dict[str, Any] = {
            # Video settings
            'VIDEO_WIDTH': int(os.getenv('VIDEO_WIDTH', '1920')),
            'VIDEO_HEIGHT': int(os.getenv('VIDEO_HEIGHT', '1080')),
            'FRAMERATE': int(os.getenv('FRAMERATE', '30')),
            'VIDEO_QUALITY': int(os.getenv('VIDEO_QUALITY', '85')),

            # Audio settings
            'AUDIO_CHANNELS': int(os.getenv('AUDIO_CHANNELS', '2')),
            'AUDIO_RATE': int(os.getenv('AUDIO_RATE', '44100')),
            'AUDIO_BITRATE': os.getenv('AUDIO_BITRATE', '128k'),

            # FFmpeg settings
            'FFMPEG_PRESET': os.getenv('FFMPEG_PRESET', 'ultrafast'),
            'FFMPEG_TUNE': os.getenv('FFMPEG_TUNE', 'zerolatency'),

            # X11 settings
            'DISPLAY': os.getenv('DISPLAY', ':99'),
            'XVFB_WHD': os.getenv('XVFB_WHD', '1920x1080x24'),

            # Web server settings
            'HOST': os.getenv('HOST', '0.0.0.0'),
            'PORT': int(os.getenv('PORT', '8000')),
            'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',

            # Input settings
            'ENABLE_MOUSE': os.getenv('ENABLE_MOUSE', 'True').lower() == 'true',
            'ENABLE_KEYBOARD': os.getenv('ENABLE_KEYBOARD', 'True').lower() == 'true',
        }

        self.logger.info("Configuration loaded successfully")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
        self.logger.debug(f"Configuration updated: {key}={value}")

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax"""
        return self.config[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set configuration value using dictionary syntax"""
        self.set(key, value) 