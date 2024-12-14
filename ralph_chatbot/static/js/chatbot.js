document.addEventListener('DOMContentLoaded', () => {
    const messagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const assetCountElem = document.getElementById('asset-count');
    const assetStatusElem = document.getElementById('asset-status');

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'assistant-message'}`;
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function updateMetrics(metrics) {
        try {
            if (metrics.assets) {
                assetCountElem.textContent = metrics.assets.total_count;
                assetStatusElem.textContent = metrics.assets.status_summary;
            }
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        appendMessage('user', message);
        input.value = '';
        
        try {
            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            appendMessage('assistant', data.response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            appendMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
    }

    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    const ralphSocket = new WebSocket(
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`
    );

    ralphSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'metrics_update' || data.type === 'initial_metrics') {
            updateMetrics(data.data);
        }
    };
});