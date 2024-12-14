class RalphMetricsConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):  # Changed from async def to def
        super().__init__(*args, **kwargs)
        self.group_name = "ralph_metrics"
        self.collector = MetricsCollector()
        self.connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 1

    async def connect(self):
        try:
            self.connected = False
            while not self.connected and self.reconnect_attempts < self.max_reconnect_attempts:
                try:
                    await self.channel_layer.group_add(
                        self.group_name,
                        self.channel_name
                    )
                    await self.accept()
                    self.connected = True
                    self.reconnect_attempts = 0
                    
                    # Send initial metrics
                    collector = MetricsCollector()
                    metrics = collector.get_all_metrics()
                    await self.send(text_data=json.dumps({
                        'type': 'initial_metrics',
                        'data': metrics
                    }))
                    
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
        try:
            self.connected = False
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for {self.channel_name}")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")

    async def receive(self, text_data):
        if not self.connected:
            logger.warning("Received message while disconnected")
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'request_metrics':
                metrics = self.collector.get_relevant_metrics(data.get('category', 'all'))
                await self.send(text_data=json.dumps({
                    'type': 'metrics_update',
                    'data': metrics
                }))
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': time.time()
                }))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def metrics_update(self, event):
        if not self.connected:
            return

        try:
            await self.send(text_data=json.dumps({
                'type': 'metrics_update',
                'data': event['data']
            }))
        except Exception as e:
            logger.error(f"Error broadcasting metrics: {str(e)}")