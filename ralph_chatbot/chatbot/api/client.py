import json
import logging

MOCK_API_TOKEN = "dummy_token"

# Dummy overall metrics
MOCK_METRICS = {
    "assets": {
        "total_count": 1234,
        "status_summary": "In Use: 1000 | Free: 200 | Damaged: 34"
    },
    "networks": {
        "status": "500 IPs used out of 1000"
    },
    "power": {
        "total_consumption": 42.5
    },
    "racks": {
        "rack_count": 10,
        "max_capacity": "100U",
        "used_capacity": "80U"
    },
    "deployments": {
        "recent_deployments": 5,
        "pending": 2
    }
}

ENDPOINT_DATA = {
    "assets/metrics/datacenter/": {
        "datacenter_assets": 500,
        "status": "In Use:300 | Free:200"
    },
    "assets/metrics/backoffice/": {
        "backoffice_assets": 734,
        "status": "In Use:700 | Free:30 | Damaged:4"
    },
    "metrics/network_metrics/": {
        "status": "500 IPs used out of 1000"
    },
    "metrics/power_metrics/": {
        "total_consumption": 42.5
    },
    "metrics/rack_metrics/": {
        "rack_count": 10,
        "max_capacity": "100U",
        "used_capacity": "80U"
    },
    "metrics/deployment_metrics/": {
        "recent_deployments": 5,
        "pending": 2
    }
}

class MockRedis:
    def __init__(self):
        self.store = {}

    def exists(self, key):
        return key in self.store

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, timeout, value):
        self.store[key] = value

class RalphAPIClient:
    def __init__(self, base_url="http://mock-ralph-backend/api", token=MOCK_API_TOKEN):
        self.base_url = base_url
        self.api_token = token
        self.redis_client = MockRedis()

    def _get_cached(self, endpoint, cache_key=None, timeout=300):
        if cache_key and self.redis_client.exists(cache_key):
            return json.loads(self.redis_client.get(cache_key))

        if endpoint == "metrics":
            data = MOCK_METRICS
        else:
            data = ENDPOINT_DATA.get(endpoint, {"message": f"No data available for endpoint {endpoint}"})

        if cache_key:
            self.redis_client.setex(cache_key, timeout, json.dumps(data))

        return data

    def fetch_metrics(self):
        return self._get_cached("metrics", cache_key="metrics_cache")

logger = logging.getLogger(__name__)
