import pyaudio
import numpy as np
import base64
import threading
import time
import logging
import sounddevice as sd

logger = logging.getLogger(__name__)

class AudioHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False
        self.stream_thread = None
        self.pyaudio = pyaudio.PyAudio()
        
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 2
        self.RATE = 44100
        
    def start_streaming(self):
        if self.running:
            return
            
        self.running = True
        self.stream_thread = threading.Thread(target=self._stream_loop)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        logger.info("Audio streaming started")
        
    def stop_streaming(self):
        self.running = False
        if self.stream_thread:
            self.stream_thread.join()
        logger.info("Audio streaming stopped")
        
    def _stream_loop(self):
        try:
            # Open stream for system audio capture
            stream = self.pyaudio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=self._get_system_audio_device()
            )
            
            while self.running:
                try:
                    # Read audio data
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    
                    # Encode and emit
                    encoded_data = base64.b64encode(audio_data.tobytes()).decode('utf-8')
                    self.socketio.emit('audio_data', {'data': encoded_data})
                    
                except Exception as e:
                    logger.error(f"Error in audio streaming loop: {str(e)}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error setting up audio stream: {str(e)}")
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
                
    def handle_mic_data(self, data):
        try:
            # Decode incoming audio data
            audio_data = base64.b64decode(data['data'])
            np_data = np.frombuffer(audio_data, dtype=np.float32)
            
            # Play the audio
            sd.play(np_data, self.RATE)
            sd.wait()
            
        except Exception as e:
            logger.error(f"Error handling microphone data: {str(e)}")
            
    def _get_system_audio_device(self):
        """Find the system audio output device"""
        try:
            for i in range(self.pyaudio.get_device_count()):
                device_info = self.pyaudio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0 and 'pulse' in device_info['name'].lower():
                    return i
            return None
        except Exception as e:
            logger.error(f"Error finding system audio device: {str(e)}")
            return None
            
    def __del__(self):
        self.stop_streaming()
        self.pyaudio.terminate() 