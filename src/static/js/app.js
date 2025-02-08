let ws = null;
let isInteractive = false;
const img = document.getElementById('videoDisplay');
const container = document.querySelector('.container');
const mousePosDiv = document.getElementById('mousePos');
const interactiveBtn = document.getElementById('interactiveMode');
const toggleAudioBtn = document.getElementById('toggleAudio');

// Sidebar elements
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const tabs = document.querySelectorAll('.tab');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');

let audioEnabled = false;
let audioBuffer = [];
let audioBufferSize = 0;
const MIN_BUFFER_SIZE = 32768; // 32KB минимальный размер буфера
let audioPlayer = null;

// Sidebar functionality
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarToggle.classList.toggle('sidebar-open');
});

// Tab switching
tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        // Remove active class from all tabs and contents
        tabs.forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        const tabName = tab.getAttribute('data-tab');
        document.getElementById(`${tabName}Tab`).classList.add('active');
    });
});

// Chat functionality
function sendChatMessage() {
    const message = chatInput.value.trim();
    if (message) {
        // Add message to chat
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to server
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                command: 'chat',
                message: message
            }));
        }
        
        chatInput.value = '';
    }
}

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

document.querySelector('.send-btn').addEventListener('click', sendChatMessage);

const showError = (message) => {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    console.error(message);
};

function initAudio() {
    audioEnabled = true;
    audioBuffer = [];
    audioBufferSize = 0;
    console.log('Audio initialized');
}

function playBufferedAudio() {
    if (!audioEnabled || audioBufferSize < MIN_BUFFER_SIZE) return;

    try {
        const concatenated = new Uint8Array(audioBufferSize);
        let offset = 0;
        for (const chunk of audioBuffer) {
            concatenated.set(chunk, offset);
            offset += chunk.length;
        }

        const blob = new Blob([concatenated], { type: 'audio/mpeg' });
        const url = URL.createObjectURL(blob);

        if (audioPlayer) {
            audioPlayer.pause();
            URL.revokeObjectURL(audioPlayer.src);
        }

        audioPlayer = new Audio();
        audioPlayer.onended = () => {
            URL.revokeObjectURL(audioPlayer.src);
            audioPlayer = null;
            // Очищаем буфер после воспроизведения
            audioBuffer = [];
            audioBufferSize = 0;
        };
        audioPlayer.onerror = (e) => {
            console.error('Audio playback error:', e);
            URL.revokeObjectURL(audioPlayer.src);
            audioPlayer = null;
            // Очищаем буфер при ошибке
            audioBuffer = [];
            audioBufferSize = 0;
        };

        audioPlayer.src = url;
        audioPlayer.play().catch(e => {
            console.error('Error starting audio playback:', e);
            URL.revokeObjectURL(url);
            audioPlayer = null;
            // Очищаем буфер при ошибке воспроизведения
            audioBuffer = [];
            audioBufferSize = 0;
        });

    } catch (e) {
        console.error('Error playing buffered audio:', e);
        audioBuffer = [];
        audioBufferSize = 0;
    }
}

function updateAudio(data) {
    if (!audioEnabled) return;

    try {
        const chunk = Uint8Array.from(atob(data), c => c.charCodeAt(0));
        audioBuffer.push(chunk);
        audioBufferSize += chunk.length;

        // Если буфер достаточно большой, начинаем воспроизведение
        if (audioBufferSize >= MIN_BUFFER_SIZE && !audioPlayer) {
            playBufferedAudio();
        }

        // Если буфер стал слишком большим, очищаем его
        if (audioBufferSize > MIN_BUFFER_SIZE * 2) {
            audioBuffer = [];
            audioBufferSize = 0;
        }
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
    const targetFrameTime = 1000 / 30; // 30 FPS
    
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
            } else if (data.type === 'chat') {
                // Handle chat response
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message';
                messageDiv.textContent = `Server: ${data.message}`;
                chatMessages.appendChild(messageDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else if (data.status === 'error') {
                showError(data.message);
            }
        } catch (e) {
            console.error('Error processing message:', e);
        }
    };
}

// Interactive mode handling
interactiveBtn.addEventListener('click', () => {
    isInteractive = !isInteractive;
    interactiveBtn.classList.toggle('active');
});

// Keyboard mapping for special keys
const specialKeys = {
    'Enter': 'Return',
    'Escape': 'Escape',
    'Backspace': 'BackSpace',
    'Tab': 'Tab',
    'Delete': 'Delete',
    'ArrowLeft': 'Left',
    'ArrowRight': 'Right',
    'ArrowUp': 'Up',
    'ArrowDown': 'Down',
    'PageUp': 'Page_Up',
    'PageDown': 'Page_Down',
    'Home': 'Home',
    'End': 'End',
    'Insert': 'Insert',
    'F1': 'F1',
    'F2': 'F2',
    'F3': 'F3',
    'F4': 'F4',
    'F5': 'F5',
    'F6': 'F6',
    'F7': 'F7',
    'F8': 'F8',
    'F9': 'F9',
    'F10': 'F10',
    'F11': 'F11',
    'F12': 'F12'
};

// Mouse position tracking
let currentX = 0;
let currentY = 0;
let lastMoveTime = 0;
const MOVE_THROTTLE = 1000 / 60; // 60Hz для стабильности

// Добавляем отладочную информацию
function updateDebugInfo(e, videoRect, x, y, details) {
    const debug = {
        mouse: `Mouse: (${e.clientX}, ${e.clientY})`,
        container: `Container: ${Math.round(container.offsetWidth)}x${Math.round(container.offsetHeight)}`,
        video: `Video: (${Math.round(videoRect.left)}, ${Math.round(videoRect.top)}) ${Math.round(videoRect.width)}x${Math.round(videoRect.height)}`,
        scale: `Scale: ${details.scaleX.toFixed(3)}x${details.scaleY.toFixed(3)}`,
        offsets: `Offsets: (${Math.round(details.offsetX)}, ${Math.round(details.offsetY)})`,
        relative: `Relative: (${Math.round(x)}, ${Math.round(y)})`,
        virtual: `Virtual: (${currentX}, ${currentY})`
    };
    mousePosDiv.innerHTML = Object.values(debug).join('<br>');
    console.log(debug);
}

container.addEventListener('mousemove', (e) => {
    if (!isInteractive) return;

    const now = performance.now();
    if (now - lastMoveTime < MOVE_THROTTLE) return;
    lastMoveTime = now;

    const videoRect = img.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    
    // Константы для виртуального экрана
    const VIRTUAL_WIDTH = 1920;
    const VIRTUAL_HEIGHT = 1080;
    const VIRTUAL_ASPECT = VIRTUAL_WIDTH / VIRTUAL_HEIGHT;
    
    // Вычисляем размеры и отступы видео в контейнере
    const containerAspect = containerRect.width / containerRect.height;
    let videoWidth, videoHeight, offsetX, offsetY;
    
    if (containerAspect > VIRTUAL_ASPECT) {
        // Контейнер шире - видео ограничено по высоте
        videoHeight = containerRect.height;
        videoWidth = videoHeight * VIRTUAL_ASPECT;
        offsetX = (containerRect.width - videoWidth) / 2;
        offsetY = 0;
    } else {
        // Контейнер уже - видео ограничено по ширине
        videoWidth = containerRect.width;
        videoHeight = videoWidth / VIRTUAL_ASPECT;
        offsetX = 0;
        offsetY = (containerRect.height - videoHeight) / 2;
    }
    
    // Вычисляем масштаб
    const scaleX = VIRTUAL_WIDTH / videoWidth;
    const scaleY = VIRTUAL_HEIGHT / videoHeight;
    
    // Вычисляем позицию курсора относительно видео
    const relativeX = e.clientX - containerRect.left - offsetX;
    const relativeY = e.clientY - containerRect.top - offsetY;
    
    // Вычисляем относительное положение в процентах
    const relativeXPercent = relativeX / videoWidth;
    const relativeYPercent = relativeY / videoHeight;
    
    // Базовое смещение зависит от масштаба и размера контейнера
    const baseOffsetX = Math.round(250 * (scaleX / 1.5));
    const baseOffsetY = Math.round(200 * (scaleY / 1.5));
    
    // Преобразуем в виртуальные координаты с адаптивным смещением
    currentX = Math.round(relativeX * scaleX) - baseOffsetX;
    currentY = Math.round(relativeY * scaleY) - baseOffsetY;
    
    // Прогрессивная коррекция зависит от положения курсора
    const horizontalCorrection = Math.min(0.4, relativeXPercent * 0.5);
    const verticalCorrection = Math.min(0.3, relativeYPercent * 0.4);
    
    // Применяем прогрессивную коррекцию
    if (currentX > VIRTUAL_WIDTH / 2) {
        currentX -= Math.round((currentX - VIRTUAL_WIDTH / 2) * horizontalCorrection);
    }
    if (currentY > VIRTUAL_HEIGHT / 2) {
        currentY -= Math.round((currentY - VIRTUAL_HEIGHT / 2) * verticalCorrection);
    }
    
    // Дополнительная коррекция для правого края
    if (relativeXPercent > 0.8) {
        currentX -= Math.round((relativeXPercent - 0.8) * videoWidth * scaleX * 0.5);
    }
    
    // Ограничиваем координаты
    currentX = Math.max(0, Math.min(VIRTUAL_WIDTH, currentX));
    currentY = Math.max(0, Math.min(VIRTUAL_HEIGHT, currentY));
    
    // Обновляем отладочную информацию с дополнительными деталями
    updateDebugInfo(e, videoRect, relativeX, relativeY, {
        scaleX,
        scaleY,
        offsetX,
        offsetY
    });
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            command: 'move',
            x: currentX,
            y: currentY
        }));
    }
});

// Click handling
container.addEventListener('mousedown', (e) => {
    if (isInteractive) {
        e.preventDefault();
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                command: 'click',
                x: Math.round(currentX),
                y: Math.round(currentY),
                button: e.button + 1 // Convert to X11 button numbering
            }));
        }
    }
});

// Keyboard handling
document.addEventListener('keydown', (e) => {
    if (!isInteractive || e.target === chatInput) return;
    
    e.preventDefault();
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        const key = specialKeys[e.key] || e.key;
        if (key.length === 1) {
            // Regular character
            ws.send(JSON.stringify({
                command: 'type',
                text: key
            }));
        } else {
            // Special key
            ws.send(JSON.stringify({
                command: 'key',
                key: key
            }));
        }
    }
});

// Audio toggle
toggleAudioBtn.addEventListener('click', () => {
    if (!audioEnabled) {
        initAudio();
        toggleAudioBtn.textContent = 'Disable Audio';
        toggleAudioBtn.classList.add('active');
    } else {
        audioEnabled = false;
        if (audioPlayer) {
            audioPlayer.pause();
            URL.revokeObjectURL(audioPlayer.src);
            audioPlayer = null;
        }
        audioBuffer = [];
        audioBufferSize = 0;
        toggleAudioBtn.textContent = 'Enable Audio';
        toggleAudioBtn.classList.remove('active');
    }
});

// Initialize WebSocket connection
connectWebSocket(); 