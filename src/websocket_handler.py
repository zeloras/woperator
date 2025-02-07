import asyncio
import json
import logging
import base64
from aiohttp import web, WSMsgType
from src.ffmpeg_stream import capture_screen, capture_audio
from src.x11_utils import run_xdotool

logger = logging.getLogger(__name__)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    logger.info('WebSocket connection opened')
    
    # Для хранения задач стриминга
    video_task = None
    audio_task = None
    
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)
                command = data.get('command')
                
                if command == 'start_stream':
                    # Останавливаем предыдущий стриминг, если есть
                    if video_task:
                        video_task.cancel()
                    if audio_task:
                        audio_task.cancel()
                    
                    # Запускаем новую задачу видео стриминга
                    async def stream_video():
                        frame_count = 0
                        start_time = asyncio.get_event_loop().time()
                        
                        try:
                            async for frame in capture_screen():
                                if ws.closed:
                                    break
                                    
                                frame_count += 1
                                if frame_count % 30 == 0:
                                    current_time = asyncio.get_event_loop().time()
                                    elapsed = current_time - start_time
                                    fps = frame_count / elapsed
                                    logger.info(f"Current FPS: {fps:.2f}")
                                
                                frame_data = base64.b64encode(frame).decode('utf-8')
                                await ws.send_json({
                                    'type': 'video',
                                    'data': frame_data
                                })
                        except Exception as e:
                            logger.error(f"Video streaming error: {str(e)}")
                            if not ws.closed:
                                await ws.send_json({
                                    'status': 'error',
                                    'message': str(e)
                                })
                    
                    # Запускаем новую задачу аудио стриминга
                    async def stream_audio():
                        try:
                            async for chunk in capture_audio():
                                if ws.closed:
                                    break
                                chunk_data = base64.b64encode(chunk).decode('utf-8')
                                await ws.send_json({
                                    'type': 'audio',
                                    'data': chunk_data
                                })
                        except Exception as e:
                            logger.error(f"Audio streaming error: {str(e)}")
                            if not ws.closed:
                                await ws.send_json({
                                    'status': 'error',
                                    'message': str(e)
                                })
                    
                    video_task = asyncio.create_task(stream_video())
                    audio_task = asyncio.create_task(stream_audio())
                
                elif command == 'click':
                    x, y = data.get('x', 0), data.get('y', 0)
                    success = await run_xdotool(['mousemove', str(x), str(y), 'click', '1'])
                    await ws.send_json({'status': 'ok' if success else 'error'})
                
                elif command == 'move':
                    x, y = data.get('x', 0), data.get('y', 0)
                    success = await run_xdotool(['mousemove', str(x), str(y)])
                    await ws.send_json({'status': 'ok' if success else 'error'})
                
                elif command == 'chat':
                    message = data.get('message', '')
                    logger.info(f"Chat message received: {message}")
                    # Заглушка - просто отправляем "ok" в ответ
                    await ws.send_json({
                        'type': 'chat',
                        'message': 'ok'
                    })
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                await ws.send_json({'status': 'error', 'message': 'Invalid JSON'})
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                await ws.send_json({'status': 'error', 'message': str(e)})
    
    # Очистка при закрытии соединения
    if video_task:
        video_task.cancel()
    if audio_task:
        audio_task.cancel()
    
    logger.info('WebSocket connection closed')
    return ws 