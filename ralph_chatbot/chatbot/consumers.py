import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .api.metrics import MetricsCollector

class RalphMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        # Add user to metrics group
        await self.channel_layer.group_add(
            "ralph_metrics",
            self.channel_name
        )
        await self.accept()
        
        # Send initial metrics
        collector = MetricsCollector()
        metrics = collector.get_all_metrics()
        await self.send(text_data=json.dumps({
            'type': 'initial_metrics',
            'data': metrics
        }))

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            "ralph_metrics",
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        if data.get('type') == 'request_metrics':
            # Get fresh metrics for specific category
            collector = MetricsCollector()
            metrics = collector.get_relevant_metrics(data.get('category', 'all'))
            await self.send(text_data=json.dumps({
                'type': 'metrics_update',
                'data': metrics
            }))

    async def metrics_update(self, event):
        """Send metrics updates to client"""
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': event['data']
        }))