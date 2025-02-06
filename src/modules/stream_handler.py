import subprocess
import threading
import logging
from typing import Optional, Generator
import cv2
import numpy as np

class StreamHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.stream_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the FFmpeg streaming process"""
        if self.is_running:
            return

        try:
            command = [
                'ffmpeg',
                '-f', 'x11grab',
                '-framerate', str(self.config['FRAMERATE']),
                '-video_size', f"{self.config['VIDEO_WIDTH']}x{self.config['VIDEO_HEIGHT']}",
                '-i', self.config['DISPLAY'],
                '-f', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-'
            ]

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8
            )
            self.is_running = True
            self.stream_thread = threading.Thread(target=self._stream_monitor)
            self.stream_thread.daemon = True  # Make thread daemon so it dies with the main process
            self.stream_thread.start()
            self.logger.info("Stream started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}")
            self.stop()

    def stop(self) -> None:
        """Stop the FFmpeg streaming process"""
        self.is_running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        self.logger.info("Stream stopped")

    def _stream_monitor(self) -> None:
        """Monitor the FFmpeg process and handle errors"""
        try:
            while self.is_running and self.process:
                error = self.process.stderr.readline()
                if error:
                    error_str = error.decode().strip()
                    if "Error" in error_str or "Failed" in error_str:
                        self.logger.error(f"FFmpeg: {error_str}")
                    else:
                        self.logger.debug(f"FFmpeg: {error_str}")
                if self.process.poll() is not None:
                    self.logger.error("FFmpeg process terminated unexpectedly")
                    self.is_running = False
                    break
        except Exception as e:
            self.logger.error(f"Error in stream monitor: {e}")
            self.is_running = False

    def generate_stream(self) -> Generator[bytes, None, None]:
        """Generate video stream frames"""
        frame_size = self.config['VIDEO_WIDTH'] * self.config['VIDEO_HEIGHT'] * 3  # RGB format
        
        while self.is_running and self.process:
            try:
                # Read raw video frame from FFmpeg output
                raw_frame = self.process.stdout.read(frame_size)
                if not raw_frame:
                    break

                # Convert raw frame to numpy array
                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((self.config['VIDEO_HEIGHT'], self.config['VIDEO_WIDTH'], 3))

                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config['VIDEO_QUALITY']])
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                self.logger.error(f"Error generating stream frame: {e}")
                break 