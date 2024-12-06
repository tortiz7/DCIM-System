from channels_redis.core import RedisChannelLayer
from channels.layers import BaseChannelLayer
import aioredis

class ScalableChannelLayer(RedisChannelLayer):
    """Custom channel layer for scaled websocket deployment"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_cluster = aioredis.Redis.from_url(
            os.getenv('REDIS_CLUSTER_URL'),
            encoding='utf-8'
        )

    async def group_add(self, group, channel):
        """Add channel to group with TTL"""
        await super().group_add(group, channel)
        await self.redis_cluster.expire(
            f"group_{group}", 
            86400  # 24 hour TTL
        )

# chatbot/settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "chatbot.scaling.ScalableChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_CLUSTER_URL")],
            "capacity": 10000,  # Max number of connections
            "expiry": 86400,    # Connection TTL
        },
    },
}