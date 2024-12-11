// chatbot/static/chatbot/js/chatbot.js

document.addEventListener('DOMContentLoaded', () => {
    const messagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const assetCountElem = document.getElementById('asset-count');
    const assetStatusElem = document.getElementById('asset-status');

    // Load metrics on page load
    async function loadMetrics() {
        try {
            const response = await fetch('/metrics/');
            const data = await response.json();
            assetCountElem.textContent = data.assets.total;
            assetStatusElem.textContent =
                `In Use: ${data.status.in_use} | Free: ${data.status.free}`;
        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    loadMetrics();

    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'assistant-message'}`;
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
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
});
