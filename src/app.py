from aiohttp import web
import asyncio
import os
import sys
import traceback
import jinja2

# Добавляем путь к src в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    TEMPLATES_DIR, STATIC_DIR, HOST, PORT
)
from src.logger import setup_logging
from src.websocket_handler import websocket_handler

# Инициализация логирования
logger = setup_logging()

# Настраиваем Jinja2
template_loader = jinja2.FileSystemLoader(str(TEMPLATES_DIR))
template_env = jinja2.Environment(loader=template_loader)

async def index(request):
    """Обработчик главной страницы"""
    try:
        logger.info("Index page requested")
        template = template_env.get_template('index.html')
        html = template.render()
        return web.Response(text=html, content_type='text/html')
    except Exception as e:
        logger.error(f"Error in index handler: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def init_app():
    """Инициализация приложения"""
    try:
        app = web.Application()
        # Добавляем обработку статических файлов
        app.router.add_static('/static', STATIC_DIR)
        app.router.add_get('/', index)
        app.router.add_get('/ws', websocket_handler)
        
        return app
    except Exception as e:
        logger.error(f"Error initializing app: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def main():
    """Точка входа в приложение"""
    try:
        logger.info(f"Starting server on http://{HOST}:{PORT}")
        app = asyncio.get_event_loop().run_until_complete(init_app())
        web.run_app(app, host=HOST, port=PORT)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main() 