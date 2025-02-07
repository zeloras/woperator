from aiohttp import web, WSMsgType
import logging
import asyncio
import os
import sys
import traceback
import json
import subprocess
import base64

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_directories():
    """Проверяем права доступа к необходимым директориям"""
    try:
        app_dir = '/app'
        stream_dir = '/app/stream'
        
        logger.info(f"Checking directory permissions...")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Current user: {os.getuid()}:{os.getgid()}")
        
        # Проверяем /app
        if not os.path.exists(app_dir):
            logger.error(f"Directory {app_dir} does not exist!")
            return False
        logger.info(f"{app_dir} permissions: {oct(os.stat(app_dir).st_mode)[-3:]}")
        
        # Создаем и проверяем /app/stream
        os.makedirs(stream_dir, exist_ok=True)
        if not os.path.exists(stream_dir):
            logger.error(f"Failed to create {stream_dir}!")
            return False
        logger.info(f"{stream_dir} permissions: {oct(os.stat(stream_dir).st_mode)[-3:]}")
        
        # Проверяем возможность записи
        try:
            test_file = os.path.join(stream_dir, 'test.txt')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("Write test successful")
        except Exception as e:
            logger.error(f"Write test failed: {str(e)}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking directories: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def run_xdotool(cmd):
    """Выполняет команду xdotool"""
    try:
        process = await asyncio.create_subprocess_exec(
            'xdotool', *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={'DISPLAY': ':99'}
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.error(f"xdotool error: {stderr.decode()}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error running xdotool: {str(e)}")
        return False

async def index(request):
    try:
        logger.info("Index page requested")
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8"/>
            <title>Stream</title>
            <style>
                body { margin: 0; background: black; font-family: Arial, sans-serif; }
                .container { position: relative; width: 100vw; height: 100vh; }
                #videoDisplay { width: 100%; height: 100%; object-fit: contain; }
                #error { 
                    position: fixed; 
                    top: 50%; 
                    left: 50%; 
                    transform: translate(-50%, -50%);
                    background: rgba(255, 0, 0, 0.8);
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    display: none;
                }
                #controls {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: rgba(0, 0, 0, 0.7);
                    padding: 10px;
                    border-radius: 5px;
                    color: white;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    z-index: 1000;
                }
                .btn {
                    background: #4CAF50;
                    border: none;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                .btn:hover {
                    background: #45a049;
                }
                .btn.active {
                    background: #f44336;
                }
                #mousePos {
                    color: white;
                    margin-top: 5px;
                }
            </style>
        </head>
            <body>
            <div class="container">
                <img id="videoDisplay" />
                <audio id="audioPlayer"></audio>
                <div id="error"></div>
                <div id="controls">
                    <button id="interactiveMode" class="btn">Interactive Mode</button>
                    <button id="toggleAudio" class="btn">Enable Audio</button>
                    <button id="closeWindow" class="btn">Close Window</button>
                    <button id="minimizeWindow" class="btn">Minimize</button>
                    <button id="maximizeWindow" class="btn">Maximize</button>
                    <div id="mousePos"></div>
                </div>
            </div>
                <script>
                let ws = null;
                let isInteractive = false;
                const img = document.getElementById('videoDisplay');
                const audio = document.getElementById('audioPlayer');
                const container = document.querySelector('.container');
                const mousePosDiv = document.getElementById('mousePos');
                const interactiveBtn = document.getElementById('interactiveMode');
                const toggleAudioBtn = document.getElementById('toggleAudio');
                
                let mediaSource = null;
                let sourceBuffer = null;
                let audioQueue = [];
                let isBufferUpdating = false;
                
                audio.muted = true;  // По умолчанию звук выключен

                const showError = (message) => {
                    const errorDiv = document.getElementById('error');
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                    console.error(message);
                };

                function initAudio() {
                    try {
                        mediaSource = new MediaSource();
                        audio.src = URL.createObjectURL(mediaSource);
                        
                        mediaSource.addEventListener('sourceopen', () => {
                            try {
                                sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
                                sourceBuffer.mode = 'sequence';
                                
                                sourceBuffer.addEventListener('updateend', () => {
                                    isBufferUpdating = false;
                                    processAudioQueue();
                                });
                                
                                console.log('Audio MediaSource initialized');
                            } catch (e) {
                                console.error('Error initializing source buffer:', e);
                                showError('Error initializing audio: ' + e.message);
                            }
                        });
                    } catch (e) {
                        console.error('Error creating MediaSource:', e);
                        showError('Error creating MediaSource: ' + e.message);
                    }
                }

                function processAudioQueue() {
                    if (!sourceBuffer || isBufferUpdating || audioQueue.length === 0) {
                        return;
                    }
                    
                    try {
                        isBufferUpdating = true;
                        const data = audioQueue.shift();
                        sourceBuffer.appendBuffer(data);
                    } catch (e) {
                        console.error('Error appending buffer:', e);
                        isBufferUpdating = false;
                    }
                }

                // Обработка аудио
                toggleAudioBtn.addEventListener('click', () => {
                    if (audio.muted) {
                        if (!mediaSource) {
                            initAudio();
                        }
                        audio.muted = false;
                        toggleAudioBtn.textContent = 'Disable Audio';
                        toggleAudioBtn.classList.add('active');
                        audio.play().catch(e => {
                            console.error('Failed to play audio:', e);
                            audio.muted = true;
                            toggleAudioBtn.textContent = 'Enable Audio';
                            toggleAudioBtn.classList.remove('active');
                            showError('Failed to play audio: ' + e.message);
                        });
                    } else {
                        audio.muted = true;
                        toggleAudioBtn.textContent = 'Enable Audio';
                        toggleAudioBtn.classList.remove('active');
                    }
                });

                function updateAudio(data) {
                    try {
                        if (!sourceBuffer) {
                            return;
                        }

                        const binary = atob(data);
                        const array = new Uint8Array(binary.length);
                        for (let i = 0; i < binary.length; i++) {
                            array[i] = binary.charCodeAt(i);
                        }
                        
                        audioQueue.push(array);
                        processAudioQueue();
                    } catch (e) {
                        console.error('Error updating audio:', e);
                    }
                }

                // WebSocket setup
                function connectWebSocket() {
                    ws = new WebSocket(`ws://${window.location.host}/ws`);
                    
                    ws.onopen = () => {
                        console.log('WebSocket connected');
                        ws.send(JSON.stringify({
                            command: 'start_stream'
                        }));
                    };
                    
                    ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        setTimeout(connectWebSocket, 1000);
                    };
                    
                    ws.onerror = (error) => console.error('WebSocket error:', error);
                    
                    let pendingFrame = null;
                    let frameUpdateScheduled = false;
                    let lastFrameTime = 0;
                    const targetFrameTime = 1000 / 120; // Целевое время между кадрами для 120 FPS
                    
                    function updateFrame(timestamp) {
                        if (pendingFrame) {
                            const timeSinceLastFrame = timestamp - lastFrameTime;
                            
                            if (timeSinceLastFrame >= targetFrameTime) {
                                img.src = pendingFrame;
                                pendingFrame = null;
                                lastFrameTime = timestamp;
                            }
                        }
                        frameUpdateScheduled = false;
                    }
                    
                    ws.onmessage = async (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            
                            if (data.type === 'video') {
                                pendingFrame = `data:image/jpeg;base64,${data.data}`;
                                if (!frameUpdateScheduled) {
                                    frameUpdateScheduled = true;
                                    requestAnimationFrame(updateFrame);
                                }
                            } else if (data.type === 'audio') {
                                updateAudio(data.data);
                            } else if (data.status === 'error') {
                                showError(data.message);
                            }
                        } catch (e) {
                            console.error('Error processing message:', e);
                        }
                    };
                }

                // Сразу подключаемся к WebSocket
                connectWebSocket();

                // Interactive mode handling
                interactiveBtn.addEventListener('click', () => {
                    isInteractive = !isInteractive;
                    interactiveBtn.classList.toggle('active');
                });

                // Mouse position tracking
                container.addEventListener('mousemove', (e) => {
                    if (isInteractive) {
                        const rect = container.getBoundingClientRect();
                        const x = Math.round((e.clientX - rect.left) * (1920 / rect.width));
                        const y = Math.round((e.clientY - rect.top) * (1080 / rect.height));
                        mousePosDiv.textContent = `Mouse: ${x}, ${y}`;
                        
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                command: 'move',
                                x: x,
                                y: y
                            }));
                        }
                    }
                });

                // Click handling
                container.addEventListener('mousedown', (e) => {
                    if (isInteractive) {
                        e.preventDefault();
                        const rect = container.getBoundingClientRect();
                        const x = Math.round((e.clientX - rect.left) * (1920 / rect.width));
                        const y = Math.round((e.clientY - rect.top) * (1080 / rect.height));
                        
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send(JSON.stringify({
                                command: 'click',
                                x: x,
                                y: y
                            }));
                        }
                    }
                });

                // Window control buttons
                document.getElementById('closeWindow').addEventListener('click', () => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            command: 'window',
                            action: 'close'
                        }));
                    }
                });

                document.getElementById('minimizeWindow').addEventListener('click', () => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            command: 'window',
                            action: 'minimize'
                        }));
                    }
                });

                document.getElementById('maximizeWindow').addEventListener('click', () => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            command: 'window',
                            action: 'maximize'
                        }));
                    }
                });
                </script>
            </body>
        </html>
        '''
        return web.Response(text=html, content_type='text/html')
    except Exception as e:
        logger.error(f"Error in index handler: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def capture_screen():
    """Захват экрана с помощью FFmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-f', 'x11grab',
            '-framerate', '60',  # Снижаем до 60 FPS для стабильности
            '-video_size', '1920x1080',
            '-draw_mouse', '1',
            '-i', ':99',
            '-c:v', 'mjpeg',
            '-q:v', '3',        # Повышаем качество
            '-pix_fmt', 'yuvj444p',  # Используем лучший формат пикселей
            '-f', 'image2pipe',
            '-threads', '4',
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
            chunk = await process.stdout.read(16384)
            if not chunk:
                break
                
            buffer.extend(chunk)
            current_time = asyncio.get_event_loop().time()
            
            while True:
                start = buffer.find(b'\xff\xd8')
                if start == -1:
                    buffer = buffer[-16384:] if len(buffer) > 16384 else buffer
                    break
                    
                end = buffer.find(b'\xff\xd9', start)
                if end == -1:
                    break
                    
                frame = buffer[start:end + 2]
                buffer = buffer[end + 2:]
                
                frame_count += 1
                if frame_count % 60 == 0:  # Логируем FPS каждые 60 кадров
                    fps = frame_count / (current_time - last_time)
                    logger.info(f"Current FPS: {fps:.2f}")
                    frame_count = 0
                    last_time = current_time
                
                frame_data = base64.b64encode(frame).decode('utf-8')
                yield frame_data
            
            await asyncio.sleep(0.001)  # Минимальная пауза для стабильности
        
        process.terminate()
        try:
            await process.wait()
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Error in capture_screen: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def generate_test_tone():
    """Генерация тестового звукового сигнала"""
    try:
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'sine=frequency=440:duration=1',  # 440Hz тон на 1 секунду
            '-f', 'pulse',
            'virtual_sink'
        ]
        
        logger.info("Generating test tone with command: %s", ' '.join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        if stderr:
            logger.info(f"FFmpeg output: {stderr.decode()}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating test tone: {str(e)}")
        return False

async def capture_audio():
    """Захват звука с помощью FFmpeg"""
    try:
        # Сначала генерируем тестовый сигнал
        await generate_test_tone()
        
        cmd = [
            'ffmpeg',
            '-f', 'pulse',
            '-i', 'virtual_sink.monitor',
            '-acodec', 'libmp3lame',
            '-b:a', '128k',
            '-ac', '2',
            '-ar', '44100',
            '-f', 'mp3',
            '-write_xing', '0',
            '-id3v2_version', '0',
            '-'
        ]
        
        logger.info("Starting audio capture with command: %s", ' '.join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Читаем первые 4KB для получения MP3 заголовка
        header = await process.stdout.read(4096)
        if header:
            yield base64.b64encode(header).decode('utf-8')
        
        chunk_size = 8192
        
        while True:
            chunk = await process.stdout.read(chunk_size)
            if not chunk:
                break
                
            chunk_data = base64.b64encode(chunk).decode('utf-8')
            yield chunk_data
            
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
                                if frame_count % 30 == 0:  # Каждые 30 кадров выводим FPS
                                    current_time = asyncio.get_event_loop().time()
                                    elapsed = current_time - start_time
                                    fps = frame_count / elapsed
                                    logger.info(f"Current FPS: {fps:.2f}")
                                
                                await ws.send_json({
                                    'type': 'video',
                                    'data': frame
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
                                await ws.send_json({
                                    'type': 'audio',
                                    'data': chunk
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
                
                elif command == 'window':
                    action = data.get('action')
                    if action == 'close':
                        success = await run_xdotool(['getactivewindow', 'windowclose'])
                        await ws.send_json({'status': 'ok' if success else 'error'})
                    elif action == 'minimize':
                        success = await run_xdotool(['getactivewindow', 'windowminimize'])
                        await ws.send_json({'status': 'ok' if success else 'error'})
                    elif action == 'maximize':
                        success = await run_xdotool(['getactivewindow', 'windowmaximize'])
                        await ws.send_json({'status': 'ok' if success else 'error'})
                
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

async def init_app():
    try:
        # Проверяем директории перед запуском
        if not check_directories():
            raise Exception("Directory checks failed")
            
        app = web.Application()
        app.router.add_get('/', index)
        app.router.add_get('/ws', websocket_handler)
        app.router.add_get('/test_audio', test_audio_handler)  # Добавляем тестовый endpoint
        
        return app
    except Exception as e:
        logger.error(f"Error initializing app: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def test_audio_handler(request):
    """Обработчик для тестирования звука"""
    try:
        success = await generate_test_tone()
        return web.json_response({
            'status': 'ok' if success else 'error',
            'message': 'Test tone generated successfully' if success else 'Failed to generate test tone'
        })
    except Exception as e:
        logger.error(f"Error in test_audio handler: {str(e)}")
        return web.json_response({
            'status': 'error',
            'message': str(e)
        }, status=500)

if __name__ == '__main__':
    try:
        logger.info("Starting server on http://0.0.0.0:8000")
        app = asyncio.get_event_loop().run_until_complete(init_app())
        web.run_app(app, host='0.0.0.0', port=8000)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1) 