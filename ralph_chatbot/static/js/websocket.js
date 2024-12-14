class RalphWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnecting = false;
    }

    connect() {
        if (this.isConnecting) return;
        
        this.isConnecting = true;
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/`;

        try {
            this.socket = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleConnectionError();
        }
    }

    setupEventHandlers() {
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.requestMetrics('all');
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error processing message:', error);
            }
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.handleConnectionError();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleConnectionError();
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'initial_metrics':
            case 'metrics_update':
                this.updateMetrics(data.data);
                break;
            case 'error':
                console.error('Received error:', data.message);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    updateMetrics(metrics) {
        if (metrics.assets) {
            document.getElementById('asset-count').textContent = 
                metrics.assets.total_count || 'N/A';
            document.getElementById('asset-status').textContent = 
                metrics.assets.status_summary || 'No status available';
        }

        if (metrics.networks) {
            document.getElementById('network-status').textContent = 
                metrics.networks.status || 'N/A';
            document.getElementById('network-detail').textContent = 
                metrics.networks.bandwidth_usage || 'No details available';
        }

        if (metrics.power) {
            document.getElementById('power-usage').textContent = 
                `${metrics.power.total_consumption || 'N/A'} kW`;
            document.getElementById('power-detail').textContent = 
                metrics.power.efficiency || 'No details available';
        }
    }

    handleConnectionError() {
        this.isConnecting = false;
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 
                this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1));
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    requestMetrics(category = 'all') {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'request_metrics',
                category: category
            }));
        }
    }

    sendMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'chat_message',
                message: message
            }));
        }
    }
}