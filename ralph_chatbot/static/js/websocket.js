class RalphWebSocket {
    constructor() {
        this.socket = null;
        this.metricsCallback = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
    }

    connect() {
        console.log('Simulating WebSocket connection with dummy data');

        // Simulate initial metrics update
        setTimeout(() => {
            const dummyData = this.getDummyMetrics();
            this.updateDashboard(dummyData);
            if (this.metricsCallback) {
                this.metricsCallback(dummyData);
            }
        }, 1000); // Simulate a short delay for connection

        // Simulate periodic metrics updates
        setInterval(() => {
            const dummyData = this.getDummyMetrics();
            this.updateDashboard(dummyData);
            if (this.metricsCallback) {
                this.metricsCallback(dummyData);
            }
        }, 30000); // Update every 30 seconds
    }

    getDummyMetrics() {
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
        // Update metrics in the chat widget
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
