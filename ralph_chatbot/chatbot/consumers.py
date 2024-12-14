from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
from .api.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class RalphMetricsConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "ralph_metrics"
        self.collector = MetricsCollector()

    async def connect(self):
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send initial metrics
        metrics = self.collector.get_all_metrics()
        await self.send(text_data=json.dumps({
            'type': 'initial_metrics',
            'data': metrics
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'request_metrics':
                metrics = self.collector.get_all_metrics()
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'data': metrics
                }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")

    async def metrics_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'data': event['data']
        }))