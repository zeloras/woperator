#!/usr/bin/env python3
from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import eventlet
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
socketio = SocketIO(app, async_mode='eventlet')

# Initialize handlers
config = Config()
stream_handler = StreamHandler(config)
input_handler = InputHandler(config)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/stream')
def stream():
    """Video streaming route"""
    return Response(
        stream_handler.generate_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('input_event')
def handle_input(data):
    """Handle input events from client"""
    input_handler.process_event(data)

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Woperator server...")
        stream_handler.start()
        socketio.run(app, host='0.0.0.0', port=8000, debug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
    finally:
        stream_handler.stop()

if __name__ == '__main__':
    main() 