import asyncio
import logging
import traceback
from src.config import (
    DISPLAY, FFMPEG_VIDEO_SETTINGS, FFMPEG_AUDIO_SETTINGS,
    WS_CHUNK_SIZE, AUDIO_CHUNK_SIZE
)

logger = logging.getLogger(__name__)

async def capture_screen():
    """Захват экрана с помощью FFmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-framerate', str(FFMPEG_VIDEO_SETTINGS['framerate']),
            '-video_size', FFMPEG_VIDEO_SETTINGS['video_size'],
            '-draw_mouse', '1',
            '-i', DISPLAY,
            '-c:v', 'mjpeg',
            '-q:v', str(FFMPEG_VIDEO_SETTINGS['quality']),
            '-pix_fmt', 'yuvj444p',
            '-f', 'image2pipe',
            '-threads', str(FFMPEG_VIDEO_SETTINGS['threads']),
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-'
        ]
        
        logger.info("Starting FFmpeg capture with command: %s", ' '.join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        buffer = bytearray()
        frame_count = 0
        last_time = asyncio.get_event_loop().time()
        
        while True:
            chunk = await process.stdout.read(WS_CHUNK_SIZE)
            if not chunk:
                break
                
            buffer.extend(chunk)
            current_time = asyncio.get_event_loop().time()
            
            while True:
                start = buffer.find(b'\xff\xd8')
                if start == -1:
                    buffer = buffer[-WS_CHUNK_SIZE:] if len(buffer) > WS_CHUNK_SIZE else buffer
                    break
                    
                end = buffer.find(b'\xff\xd9', start)
                if end == -1:
                    break
                    
                frame = buffer[start:end + 2]
                buffer = buffer[end + 2:]
                
                frame_count += 1
                if frame_count % 60 == 0:
                    fps = frame_count / (current_time - last_time)
                    logger.info(f"Current FPS: {fps:.2f}")
                    frame_count = 0
                    last_time = current_time
                
                yield frame
            
            await asyncio.sleep(0.001)
        
        process.terminate()
        try:
            await process.wait()
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Error in capture_screen: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def capture_audio():
    """Захват звука с помощью FFmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-f', 'pulse',
            '-i', 'virtual_sink.monitor',
            '-acodec', 'libmp3lame',
            '-ar', '44100',
            '-ac', '2',
            '-b:a', '128k',
            '-bufsize', '128k',
            '-maxrate', '128k',
            '-minrate', '128k',
            '-f', 'mp3',
            '-'
        ]
        
        logger.info("Starting audio capture with command: %s", ' '.join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        while True:
            chunk = await process.stdout.read(AUDIO_CHUNK_SIZE)
            if not chunk:
                break
                
            yield chunk
            await asyncio.sleep(0.02)
        
        process.terminate()
        try:
            await process.wait()
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Error in capture_audio: {str(e)}")
        logger.error(traceback.format_exc())
        raise 