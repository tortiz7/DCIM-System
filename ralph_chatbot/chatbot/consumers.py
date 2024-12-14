import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
from .api.metrics import MetricsCollector
from django.conf import settings

logger = logging.getLogger(__name__)

class RalphMetricsConsumer(AsyncWebsocketConsumer):
    async def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.group_name = "ralph_metrics"
        self.collector = MetricsCollector()
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 1  # seconds

    async def connect(self):
        """Handle WebSocket connection with retry logic"""
        try:
            self.connected = False
            while not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    # Attempt to add to channel layer group
                    await self.channel_layer.group_add(
                        self.group_name,
                        self.channel_name
                    )
                    
                    # Accept the connection
                    await self.accept()
                    self.connected = True
                    
                    # Reset reconnect attempts on successful connection
                    self.reconnect_attempts = 0
                    
                    # Send initial metrics
                    await self.send_initial_metrics()
                    
                    logger.info(f"WebSocket connection established for {self.channel_name}")
                    return

                except Exception as e:
                    self.reconnect_attempts += 1
                    logger.warning(f"Connection attempt {self.reconnect_attempts} failed: {str(e)}")
                    if self.reconnect_attempts < self.max_reconnect_attempts:
                        await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
                    else:
                        logger.error("Max reconnection attempts reached")
                        await self.close(code=1011)
                        raise StopConsumer()

        except Exception as e:
            logger.error(f"Fatal connection error: {str(e)}")
            await self.close(code=1011)
            raise StopConsumer()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            self.connected = False
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for {self.channel_name} with code {close_code}")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages with error handling"""
        if not self.connected:
            logger.warning("Received message while disconnected")
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_metrics':
                await self.handle_metrics_request(data)
            elif message_type == 'ping':
                await self.handle_ping()
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                await self.send_error("Unknown message type")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send_error(f"Error processing message: {str(e)}")

    async def metrics_update(self, event):
        """Broadcast metrics updates with error handling"""
        if not self.connected:
            return

        try:
            await self.send(text_data=json.dumps({
                'type': 'metrics_update',
                'data': event['data'],
                'timestamp': event.get('timestamp')
            }))
        except Exception as e:
            logger.error(f"Error broadcasting metrics: {str(e)}")
            await self.send_error("Error broadcasting metrics")

    async def send_initial_metrics(self):
        """Send initial metrics to client"""
        try:
            metrics = self.collector.get_all_metrics()
            await self.send(text_data=json.dumps({
                'type': 'initial_metrics',
                'data': metrics,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error sending initial metrics: {str(e)}")
            await self.send_error("Error fetching initial metrics")

    async def handle_metrics_request(self, data):
        """Handle specific metrics requests"""
        try:
            category = data.get('category', 'all')
            metrics = self.collector.get_relevant_metrics(category)
            await self.send(text_data=json.dumps({
                'type': 'metrics_update',
                'data': metrics,
                'category': category,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error handling metrics request: {str(e)}")
            await self.send_error(f"Error fetching {data.get('category', 'all')} metrics")

    async def handle_ping(self):
        """Handle ping messages to maintain connection"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error handling ping: {str(e)}")

    async def send_error(self, message):
        """Send error message to client"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': message,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")

    @property
    def channel_layer(self):
        """Get channel layer with error handling"""
        if not hasattr(self, "_channel_layer"):
            raise ValueError("Channel layer not initialized")
        return self._channel_layer