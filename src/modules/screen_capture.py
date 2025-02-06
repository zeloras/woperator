import cv2
import numpy as np
import pyautogui
import base64
import threading
import time
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class ScreenCapture:
    def __init__(self, socketio, fps=30):
        self.socketio = socketio
        self.running = False
        self.fps = fps
        self.capture_thread = None
        
    def start_capture(self):
        if self.running:
            return
            
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        logger.info("Screen capture started")
        
    def stop_capture(self):
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        logger.info("Screen capture stopped")
        
    def _capture_loop(self):
        while self.running:
            try:
                # Capture the screen
                screenshot = pyautogui.screenshot()
                
                # Convert to JPEG
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='JPEG', quality=70)
                img_byte_arr = img_byte_arr.getvalue()
                
                # Encode as base64
                base64_frame = base64.b64encode(img_byte_arr).decode('utf-8')
                
                # Emit the frame
                self.socketio.emit('screen_frame', {'data': base64_frame})
                
                # Control FPS
                time.sleep(1/self.fps)
                
            except Exception as e:
                logger.error(f"Error in screen capture: {str(e)}")
                time.sleep(1)  # Prevent rapid error logging 