from flask import Flask, render_template
from flask_socketio import SocketIO
import mss
import base64
from PIL import Image
from io import BytesIO
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def capture_screen():
    with mss.mss() as sct:
        while True:
            screenshot = sct.grab(sct.monitors[0])
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=70)
            b64_str = base64.b64encode(buffer.getvalue()).decode()
            socketio.emit('screen', {'data': b64_str})
            time.sleep(1/30)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    thread = threading.Thread(target=capture_screen)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)