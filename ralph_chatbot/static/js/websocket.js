class RalphWebSocket {
    constructor() {
        this.socket = null;
        this.metricsCallback = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.isConnecting = false;
    }

    connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;

        try {
            this.socket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/`);

            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                // Request initial metrics
                this.requestMetrics('all');
            };

            this.socket.onclose = () => {
                console.log('WebSocket closed, attempting reconnect...');
                this.isConnecting = false;
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => this.connect(), 5000 * Math.pow(2, this.reconnectAttempts));
                    this.reconnectAttempts++;
                }
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'metrics_update' || data.type === 'initial_metrics') {
                        this.updateDashboard(data.data);
                        if (this.metricsCallback) {
                            this.metricsCallback(data.data);
                        }
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
            };
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.isConnecting = false;
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

    updateDashboard(data) {
        // Update asset metrics
        const assetCount = document.getElementById('asset-count');
        const assetStatus = document.getElementById('asset-status');
        if (data.assets) {
            if (assetCount) assetCount.textContent = data.assets.total_count || 'N/A';
            if (assetStatus) assetStatus.textContent = data.assets.status_summary || 'No status available';
        }

        // Update network metrics
        const networkStatus = document.getElementById('network-status');
        if (data.networks && networkStatus) {
            networkStatus.textContent = data.networks.status || 'N/A';
        }

        // Update power metrics
        const powerUsage = document.getElementById('power-usage');
        if (data.power && powerUsage) {
            powerUsage.textContent = data.power.total_consumption ? 
                `${data.power.total_consumption} kW` : 'N/A';
        }
    }

    setMetricsCallback(callback) {
        this.metricsCallback = callback;
    }
}

// Initialize and connect WebSocket when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const ralphSocket = new RalphWebSocket();
    ralphSocket.connect();
    
    // Refresh metrics periodically
    setInterval(() => {
        ralphSocket.requestMetrics('all');
    }, 30000);
});