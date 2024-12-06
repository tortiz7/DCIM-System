from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .api.metrics import MetricsCollector
import asyncio
import threading

class MetricsBroadcasting:
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.collector = MetricsCollector()
        self.should_run = True

    async def broadcast_metrics(self):
        """Broadcast metrics updates to all connected clients"""
        while self.should_run:
            metrics = self.collector.get_all_metrics()
            await self.channel_layer.group_send(
                "ralph_metrics",
                {
                    "type": "metrics_update",
                    "data": metrics
                }
            )
            await asyncio.sleep(30)  # Update every 30 seconds

    def start_broadcasting(self):
        """Start broadcasting metrics in a background thread"""
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.broadcast_metrics())
            
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def stop_broadcasting(self):
        """Stop broadcasting metrics"""
        self.should_run = False