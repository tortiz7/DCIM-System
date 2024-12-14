class RalphWebSocket {
    constructor() {
        this.socket = null;
        this.metricsCallback = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }

    connect() {
        try {
            // Establish WebSocket connection
            this.socket = new WebSocket(`ws://${window.location.host}/ws/chat/`);

            // Handle WebSocket open event
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0; // Reset reconnect attempts
            };

            // Handle WebSocket close event
            this.socket.onclose = () => {
                console.log('WebSocket closed, attempting reconnect...');
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    setTimeout(() => this.connect(), 5000); // Retry connection
                    this.reconnectAttempts++;
                } else {
                    console.error('Max reconnect attempts reached');
                }
            };

            // Handle incoming messages
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'metrics_update' || data.type === 'initial_metrics') {
                    this.updateDashboard(data.data);
                    if (this.metricsCallback) {
                        this.metricsCallback(data.data);
                    }
                }
            };

            // Handle errors
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('WebSocket connection error:', error);
        }
    }

    getDummyMetrics() {
        // Simulate metrics for development purposes
        return {
            type: 'metrics_update',
            data: {
                assets: {
                    total_count: Math.floor(Math.random() * 1000),
                    status_summary: 'All systems operational',
                },
                networks: {
                    status: 'Stable',
                },
                power: {
                    total_consumption: (Math.random() * 100).toFixed(2),
                },
            },
        };
    }

    updateDashboard(data) {
        // Update the metrics on the dashboard
        if (data.type === 'metrics_update') {
            const metrics = data.data;

            // Update asset metrics
            if (metrics.assets) {
                const assetCount = document.getElementById('asset-count');
                const assetStatus = document.getElementById('asset-status');
                if (assetCount) assetCount.textContent = metrics.assets.total_count;
                if (assetStatus) assetStatus.textContent = metrics.assets.status_summary;
            }

            // Update network metrics
            if (metrics.networks) {
                const networkStatus = document.getElementById('network-status');
                if (networkStatus) networkStatus.textContent = metrics.networks.status;
            }

            // Update power metrics
            if (metrics.power) {
                const powerUsage = document.getElementById('power-usage');
                if (powerUsage) powerUsage.textContent = `${metrics.power.total_consumption} kW`;
            }
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
});
