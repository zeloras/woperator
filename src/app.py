import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
from modules.screen_capture import ScreenCapture
from modules.input_handler import InputHandler
from modules.audio_handler import AudioHandler
from modules.webcam_handler import WebcamHandler
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize handlers
screen_capture = ScreenCapture(socketio)
input_handler = InputHandler()
audio_handler = AudioHandler(socketio)
webcam_handler = WebcamHandler(socketio)

@app.route('/')
def index():
    return render_template('index.html')

# Screen sharing events
@socketio.on('request_screen')
def handle_screen_request():
    screen_capture.start_capture()

@socketio.on('stop_screen')
def handle_screen_stop():
    screen_capture.stop_capture()

# Input events
@socketio.on('mouse_event')
def handle_mouse_event(data):
    input_handler.handle_mouse(data)

@socketio.on('keyboard_event')
def handle_keyboard_event(data):
    input_handler.handle_keyboard(data)

@socketio.on('keyboard_special')
def handle_keyboard_special(data):
    input_handler.handle_special_keys(data)

# Audio events
@socketio.on('start_audio')
def handle_start_audio():
    audio_handler.start_streaming()

@socketio.on('stop_audio')
def handle_stop_audio():
    audio_handler.stop_streaming()

@socketio.on('mic_data')
def handle_mic_data(data):
    audio_handler.handle_mic_data(data)

# Webcam events
@socketio.on('start_webcam')
def handle_start_webcam():
    webcam_handler.start_streaming()

@socketio.on('stop_webcam')
def handle_stop_webcam():
    webcam_handler.stop_streaming()

@socketio.on('webcam_client')
def handle_webcam_data(data):
    webcam_handler.handle_client_data(data)

# Connection events
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')
    screen_capture.stop_capture()
    audio_handler.stop_streaming()
    webcam_handler.stop_streaming()

if __name__ == '__main__':
    with app.app_context():
        socketio.run(app, host='0.0.0.0', port=8000, debug=True) 