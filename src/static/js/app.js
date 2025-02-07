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