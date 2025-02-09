import os
import sys
import logging
import time
import socket
from flask import Flask, render_template
from websockify.websocketproxy import WebSocketProxy
import threading
import pyaudio
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__, 
    template_folder=os.path.join(PROJECT_ROOT, 'web/templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'static'),
    static_url_path='/static'
)

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 2
RATE = 44100

def wait_for_port(port, timeout=30):
    """Wait for a port to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                s.close()
                return True
        except OSError:
            logger.info(f"Port {port} is still in use, waiting...")
            time.sleep(1)
    return False

class VNCProxy(WebSocketProxy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_stream = None
        self.init_audio()

    def init_audio(self):
        try:
            self.audio = pyaudio.PyAudio()
            # Try to find a working audio device
            device_count = self.audio.get_device_count()
            device_index = None
            
            for i in range(device_count):
                try:
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:
                        device_index = i
                        break
                except Exception:
                    continue

            if device_index is not None:
                self.audio_stream = self.audio.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=CHUNK
                )
                logger.info(f"Audio initialized using device index {device_index}")
            else:
                logger.warning("No suitable audio input device found")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")

    def new_client(self):
        """Called after a new WebSocket connection has been established."""
        super().new_client()
        if hasattr(self, 'audio_stream') and self.audio_stream:
            threading.Thread(target=self.stream_audio, daemon=True).start()

    def stream_audio(self):
        """Stream audio data to the client."""
        try:
            while self.audio_stream and not self.terminate:
                try:
                    data = self.audio_stream.read(CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    # Process and send audio data to client
                except IOError as e:
                    logger.warning(f"Audio stream read error: {e}")
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

def run_websockify():
    """Run the VNC websocket proxy."""
    # Wait for ports to be available
    if not wait_for_port(6080):
        logger.error("Timeout waiting for port 6080")
        return

    server = VNCProxy(
        target_host='0.0.0.0',
        target_port=5900,
        listen_host='0.0.0.0',
        listen_port=6080,
        web=False,
        daemon=False,
        ssl_only=False
    )
    
    try:
        server.start_server()
    except Exception as e:
        logger.error(f"Failed to start websockify server: {e}")

def main():
    """Main entry point."""
    # Start Flask application in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=6081))
    flask_thread.daemon = True
    flask_thread.start()

    # Run websockify in the main thread
    run_websockify()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        sys.exit(0) 