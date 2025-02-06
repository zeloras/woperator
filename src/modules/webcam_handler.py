import cv2
import numpy as np
import base64
import threading
import time
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

class WebcamHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.running = False
        self.stream_thread = None
        self.cap = None
        
    def start_streaming(self):
        if self.running:
            return
            
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("Failed to open webcam")
                return
                
            self.running = True
            self.stream_thread = threading.Thread(target=self._stream_loop)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            logger.info("Webcam streaming started")
            
        except Exception as e:
            logger.error(f"Error starting webcam: {str(e)}")
            
    def stop_streaming(self):
        self.running = False
        if self.stream_thread:
            self.stream_thread.join()
        if self.cap:
            self.cap.release()
        self.cap = None
        logger.info("Webcam streaming stopped")
        
    def _stream_loop(self):
        while self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("Failed to read webcam frame")
                    break
                    
                # Convert frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                
                # Convert to base64
                base64_frame = base64.b64encode(buffer).decode('utf-8')
                
                # Emit the frame
                self.socketio.emit('webcam_frame', {'data': base64_frame})
                
                # Control FPS
                time.sleep(1/30)  # 30 FPS
                
            except Exception as e:
                logger.error(f"Error in webcam streaming: {str(e)}")
                time.sleep(1)
                
    def handle_client_data(self, data):
        """Handle incoming webcam data from client"""
        try:
            # Decode base64 image
            img_data = base64.b64decode(data['data'])
            
            # Convert to OpenCV format
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # Process frame if needed
                # For now, just re-encode and broadcast to other clients
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                base64_frame = base64.b64encode(buffer).decode('utf-8')
                self.socketio.emit('webcam_frame', {'data': base64_frame})
                
        except Exception as e:
            logger.error(f"Error handling client webcam data: {str(e)}")
            
    def __del__(self):
        self.stop_streaming() 