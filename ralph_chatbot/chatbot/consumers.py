import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .api.metrics import MetricsCollector

class RalphMetricsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        await self.channel_layer.group_add(
            "ralph_metrics",
            self.channel_name
        )
        await self.accept()
        
        # Send initial mock metrics
        collector = MetricsCollector()
        metrics = collector.get_all_metrics()
        await self.send(text_data=json.dumps({
            'type': 'initial_metrics',
            'data': metrics
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "ralph_metrics",
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            collector = MetricsCollector()
            
            if data.get('type') == 'request_metrics':
                metrics = collector.get_relevant_metrics(data.get('category', 'all'))
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'data': metrics
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def metrics_update(self, event):
        """Broadcast metrics updates"""
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': event['data']
        }))