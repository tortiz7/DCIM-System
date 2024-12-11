import json
import logging

# Mock Redis-like storage for caching in memory
class MockRedis:
    def __init__(self):
        self.store = {}

    def exists(self, key):
        return key in self.store

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, timeout, value):
        self.store[key] = value

# RalphAPIClient implementation
class RalphAPIClient:
    def __init__(self):
        self.base_url = "http://mock-ralph-backend/api"  # Placeholder base URL
        self.api_token = MOCK_API_TOKEN
        self.redis_client = MockRedis()  # Use MockRedis for in-memory caching

    def _get_cached(self, endpoint, cache_key=None, timeout=300):
        """
        Mocked method to simulate fetching data with caching.
        """
        if cache_key and self.redis_client.exists(cache_key):
            return json.loads(self.redis_client.get(cache_key))

        # Simulate API response
        if endpoint == "metrics":
            data = MOCK_METRICS
        else:
            data = {"message": f"No data available for endpoint {endpoint}"}

        # Cache the response
        if cache_key:
            self.redis_client.setex(
                cache_key,
                timeout,
                json.dumps(data)
            )

        return data

    def fetch_metrics(self):
        """
        Fetch metrics using the mocked endpoint.
        """
        return self._get_cached("metrics", cache_key="metrics_cache")

# Logging setup
logger = logging.getLogger(__name__)

# Example usage
if __name__ == "__main__":
    client = RalphAPIClient()
    metrics = client.fetch_metrics()
    logger.info(f"Fetched metrics: {metrics}")
