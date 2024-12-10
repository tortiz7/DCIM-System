class RalphAssistant {
    constructor() {
        this.socket = null;
        this.messageQueue = [];
    }

    initialize() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadMetrics();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = new WebSocket(`${protocol}//${window.location.host}/ws/assistant/`);
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update') {
                this.updateMetrics(data.metrics);
            }
        };
    }

    setupEventListeners() {
        const sendButton = document.getElementById('send-message');
        const input = document.getElementById('chat-input');

        sendButton.addEventListener('click', () => this.sendMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }

    async loadMetrics() {
        // Adjust the URL to match how you mounted assistant's urls. If /assistant/ is correct, use it:
        const response = await fetch('/assistant/metrics/');
        const data = await response.json();
        this.updateMetrics(data);
    }

    updateMetrics(metrics) {
        document.getElementById('asset-count').textContent = metrics.assets.total;
        document.getElementById('asset-status').textContent =
            `In Use: ${metrics.status.in_use} | Free: ${metrics.status.free}`;
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (!message) return;

        this.appendMessage('user', message);
        input.value = '';

        const response = await fetch('/assistant/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        this.appendMessage('assistant', data.response);
    }

    appendMessage(sender, text) {
        const messages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender} mb-4 ${sender === 'user' ? 'text-right' : 'text-left'}`;
        
        const bubble = document.createElement('div');
        bubble.className = `inline-block p-3 rounded-lg ${sender === 'user' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-200 text-gray-900'}`;
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messages.appendChild(messageDiv);
        messages.scrollTop = messages.scrollHeight;
    }
}
