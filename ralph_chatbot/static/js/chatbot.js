// chatbot/static/chatbot/js/chatbot.js
document.addEventListener('DOMContentLoaded', () => {
    const messagesDiv = document.getElementById('chat-messages');
    const input = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const assetCountElem = document.getElementById('asset-count');
    const assetStatusElem = document.getElementById('asset-status');

    // Helper function to append messages to the chat window
    function appendMessage(sender, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender === 'user' ? 'user-message' : 'assistant-message'}`;
        messageDiv.textContent = text;
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the latest message
    }

    // Function to send a message to the backend
    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return; // Do nothing if input is empty

        appendMessage('user', message);
        input.value = ''; // Clear input field after sending

        try {
            // Get CSRF token from the DOM
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                throw new Error('CSRF token not found.');
            }

            const response = await fetch('/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ 
                    question: message,
                    timestamp: new Date().toISOString()
                }),
                credentials: 'include' // Include cookies in the request
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            // Append the assistant's response
            appendMessage('assistant', data.response);
        } catch (error) {
            console.error('Error:', error);
            appendMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
    }

    // Function to get the CSRF token
    function getCSRFToken() {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }

        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }

        console.error('CSRF token not found!');
        return null;
    }

    // Function to update metrics in the UI
    function updateMetrics(metrics) {
        try {
            if (metrics.assets) {
                assetCountElem.textContent = metrics.assets.total_count || 'N/A';
                assetStatusElem.textContent = metrics.assets.status_summary || 'N/A';
            }
        } catch (error) {
            console.error('Error updating metrics:', error);
        }
    }

    // Event listeners for user interactions
    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Initialize WebSocket connection
    const ralphSocket = new WebSocket(
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`
    );

    // Handle WebSocket messages
    ralphSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'metrics_update' || data.type === 'initial_metrics') {
                updateMetrics(data.data);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    // Handle WebSocket errors
    ralphSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    // Handle WebSocket closure
    ralphSocket.onclose = (event) => {
        console.warn('WebSocket connection closed:', event);
    };
});
