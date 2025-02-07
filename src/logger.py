import logging
import sys
from src.config import LOG_LEVEL, LOG_FORMAT

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Отключаем лишние логи от aiohttp
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    logging.getLogger('aiohttp.server').setLevel(logging.WARNING)
    
    return logging.getLogger('woperator') 