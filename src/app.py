#!/usr/bin/env python3
# Monkey patch должен быть первым импортом
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, Response, request
from flask_socketio import SocketIO, disconnect
from modules.stream_handler import StreamHandler
from modules.input_handler import InputHandler
from modules.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'woperator_secret_key'

# Initialize Socket.IO with specific settings
socketio = SocketIO(
    app,
    async_mode='eventlet',
    ping_timeout=10,
    ping_interval=5,
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True
)

# Initialize handlers
config = Config()
stream_handler = None
input_handler = None

def init_handlers():
    """Initialize handlers with application context"""
    global stream_handler, input_handler
    with app.app_context():
        stream_handler = StreamHandler(config)
        input_handler = InputHandler(config)

# Store active clients
active_clients = set()

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/stream')
def stream():
    """Video streaming route"""
    try:
        client_id = request.remote_addr
        if client_id in active_clients:
            logger.info(f"Client {client_id} already has an active stream")
            return "Multiple streams not allowed", 429
        
        active_clients.add(client_id)
        logger.info(f"New stream request from {client_id}")
        
        return stream_handler.get_stream(client_id)
    except Exception as e:
        logger.error(f"Stream error: {e}")
        if client_id in active_clients:
            active_clients.remove(client_id)
        return str(e), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.remote_addr
    logger.info(f'Client connected: {client_id}')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.remote_addr
    logger.info(f'Client disconnected: {client_id}')
    if client_id in active_clients:
        active_clients.remove(client_id)
        stream_handler.cleanup_client(client_id)

@socketio.on('input_event')
def handle_input(data):
    """Handle input events from client"""
    input_handler.process_event(data)

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Woperator server...")
        init_handlers()
        stream_handler.start()
        socketio.run(
            app,
            host='0.0.0.0',
            port=8000,
            debug=True,
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        if stream_handler:
            stream_handler.stop()

if __name__ == '__main__':
    main() 