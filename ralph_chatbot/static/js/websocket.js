class RalphWebSocket {
    constructor() {
        this.socket = null;
        this.metricsCallback = null;
    }

    connect() {
        // Use relative path for WebSocket - will work with NGINX
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/metrics/`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.requestMetrics('all');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.metricsCallback) {
                this.metricsCallback(data);
            }
            this.updateDashboard(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connect(), 5000);
        };
    }

    requestMetrics(category) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'request_metrics',
                category: category
            }));
        }
    }

    updateDashboard(data) {
        // Update metrics in the chat widget
        if (data.type === 'metrics_update') {
            const metrics = data.data;
            
            // Update asset metrics
            if (metrics.assets) {
                document.getElementById('asset-count').textContent = 
                    metrics.assets.total_count;
                document.getElementById('asset-status').textContent = 
                    metrics.assets.status_summary;
            }

            // Update network metrics
            if (metrics.networks) {
                document.getElementById('network-status').textContent = 
                    metrics.networks.status;
            }

            // Update power metrics
            if (metrics.power) {
                document.getElementById('power-usage').textContent = 
                    `${metrics.power.total_consumption} kW`;
            }
        }
    }

    setMetricsCallback(callback) {
        this.metricsCallback = callback;
    }
}