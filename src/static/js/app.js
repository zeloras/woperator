let ws = null;
let isInteractive = false;
const img = document.getElementById('videoDisplay');
const audio = document.getElementById('audioPlayer');
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

let mediaSource = null;
let sourceBuffer = null;
let audioQueue = [];
let isBufferUpdating = false;

audio.muted = true;  // По умолчанию звук выключен

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

// Initialize WebSocket connection
connectWebSocket(); 