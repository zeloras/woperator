import subprocess
import threading
import logging
from typing import Optional, Generator
import cv2
import numpy as np
import time
from flask import Response, current_app
import queue
from contextlib import suppress

class StreamHandler:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.stream_thread: Optional[threading.Thread] = None
        self.active_streams = {}  # Changed to dict to store client info
        self.stream_lock = threading.Lock()
        self.frame_buffer = queue.Queue(maxsize=30)
        self.frame_thread: Optional[threading.Thread] = None
        self.last_frame = None  # Store last frame for new connections

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
            
            # Start frame reading thread
            self.frame_thread = threading.Thread(target=self._read_frames)
            self.frame_thread.daemon = True
            self.frame_thread.start()
            
            # Start monitoring thread
            self.stream_thread = threading.Thread(target=self._stream_monitor)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            
            self.logger.info("Stream started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}")
            self.stop()

    def stop(self) -> None:
        """Stop the FFmpeg streaming process"""
        self.is_running = False
        
        # Clear frame buffer
        with suppress(queue.Empty):
            while True:
                self.frame_buffer.get_nowait()
        
        with self.stream_lock:
            self.active_streams.clear()
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
        
        self.last_frame = None
        self.logger.info("Stream stopped")

    def cleanup_client(self, client_id: str) -> None:
        """Clean up resources for a disconnected client"""
        with self.stream_lock:
            if client_id in self.active_streams:
                del self.active_streams[client_id]
                self.logger.info(f"Cleaned up resources for client {client_id}")

    def _stream_monitor(self) -> None:
        """Monitor the FFmpeg process and handle errors"""
        while self.is_running and self.process:
            try:
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
                
                time.sleep(0.1)  # Prevent high CPU usage
            except Exception as e:
                self.logger.error(f"Error in stream monitor: {e}")
                self.is_running = False
                break

    def _read_frames(self) -> None:
        """Read frames from FFmpeg output and store in buffer"""
        frame_size = self.config['VIDEO_WIDTH'] * self.config['VIDEO_HEIGHT'] * 3
        
        while self.is_running and self.process:
            try:
                raw_frame = self.process.stdout.read(frame_size)
                if not raw_frame:
                    break

                frame = np.frombuffer(raw_frame, dtype=np.uint8)
                frame = frame.reshape((self.config['VIDEO_HEIGHT'], self.config['VIDEO_WIDTH'], 3))

                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config['VIDEO_QUALITY']])
                frame_bytes = buffer.tobytes()
                
                self.last_frame = frame_bytes

                try:
                    self.frame_buffer.put_nowait(frame_bytes)
                except queue.Full:
                    try:
                        self.frame_buffer.get_nowait()  # Remove oldest frame
                        self.frame_buffer.put_nowait(frame_bytes)
                    except queue.Empty:
                        pass

            except Exception as e:
                self.logger.error(f"Error reading frame: {e}")
                if not self.is_running:
                    break
                time.sleep(0.1)  # Brief pause before retry

    def generate_frames(self, client_id: str) -> Generator[bytes, None, None]:
        """Generate video frames for a specific client"""
        with self.stream_lock:
            if client_id in self.active_streams:
                self.logger.warning(f"Client {client_id} already has an active stream")
                return
            self.active_streams[client_id] = time.time()

        try:
            # Send last frame immediately if available
            if self.last_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.last_frame + b'\r\n')

            while self.is_running and client_id in self.active_streams:
                try:
                    frame_bytes = self.frame_buffer.get(timeout=1.0)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                except queue.Empty:
                    continue
                except (BrokenPipeError, ConnectionResetError) as e:
                    self.logger.info(f"Client {client_id} disconnected: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Error generating frame for client {client_id}: {e}")
                    break

        finally:
            self.cleanup_client(client_id)

    def get_stream(self, client_id: str) -> Response:
        """Get a video stream response for a specific client"""
        if not self.is_running:
            self.logger.error("Stream is not running")
            raise RuntimeError("Stream is not running")
            
        return Response(
            self.generate_frames(client_id),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        ) 