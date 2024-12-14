import json
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache

logger = logging.getLogger(__name__)

MOCK_API_TOKEN = "dummy_token"

# Enhanced mock metrics with more detailed data
MOCK_METRICS = {
    "assets": {
        "total_count": 1234,
        "status_summary": "In Use: 1000 | Free: 200 | Damaged: 34",
        "recent_activity": "5 new assets added today",
        "health_status": {
            "healthy": 1100,
            "warning": 100,
            "critical": 34
        }
    },
    "networks": {
        "status": "500 IPs used out of 1000",
        "bandwidth_usage": "75%",
        "active_connections": 850,
        "alerts": "No critical issues"
    },
    "power": {
        "total_consumption": 42.5,
        "efficiency": "92%",
        "peak_usage": "45.8 kW",
        "trend": "Stable"
    },
    "racks": {
        "rack_count": 10,
        "max_capacity": "100U",
        "used_capacity": "80U",
        "temperature": "23°C",
        "cooling_status": "Optimal"
    },
    "deployments": {
        "recent_deployments": 5,
        "pending": 2,
        "success_rate": "98%",
        "average_time": "45 minutes"
    }
}

# Enhanced endpoint-specific data
ENDPOINT_DATA = {
    "assets/metrics/datacenter/": {
        "datacenter_assets": 500,
        "status": "In Use: 300 | Free: 200",
        "temperature": "23°C",
        "health": "98% Optimal"
    },
    "assets/metrics/backoffice/": {
        "backoffice_assets": 734,
        "status": "In Use: 700 | Free: 30 | Damaged: 4",
        "recent_changes": "12 new assignments"
    },
    "metrics/network_metrics/": {
        "status": "500 IPs used out of 1000",
        "bandwidth": "75% utilization",
        "active_vlans": 24,
        "security_status": "Normal"
    },
    "metrics/power_metrics/": {
        "total_consumption": 42.5,
        "peak_time": "14:00 UTC",
        "efficiency_rating": "A+",
        "carbon_footprint": "Reduced by 15%"
    },
    "metrics/rack_metrics/": {
        "rack_count": 10,
        "max_capacity": "100U",
        "used_capacity": "80U",
        "hotspots": "None detected"
    },
    "metrics/deployment_metrics/": {
        "recent_deployments": 5,
        "pending": 2,
        "success_rate": "98%",
        "automation_savings": "120 hours/month"
    }
}

class MockRedis:
    """Enhanced mock Redis implementation with TTL support"""
    def __init__(self):
        self.store = {}
        self.ttls = {}

    def exists(self, key: str) -> bool:
        if key in self.ttls and self.ttls[key] < time.time():
            del self.store[key]
            del self.ttls[key]
            return False
        return key in self.store

    def get(self, key: str) -> Optional[str]:
        if self.exists(key):
            return self.store.get(key)
        return None

    def setex(self, key: str, timeout: int, value: str) -> None:
        self.store[key] = value
        self.ttls[key] = time.time() + timeout

class RalphAPIClient:
    """Enhanced Ralph API client with better caching and error handling"""
    def __init__(self, base_url: str = "http://mock-ralph-backend/api", token: str = MOCK_API_TOKEN):
        self.base_url = base_url
        self.api_token = token
        self.redis_client = MockRedis()
        self.cache_timeout = 300  # 5 minutes default cache timeout

    def _get_cached(self, endpoint: str, cache_key: Optional[str] = None, timeout: int = 300) -> Dict[str, Any]:
        """Get data with caching support and error handling"""
        try:
            if cache_key:
                cached_data = cache.get(cache_key)
                if cached_data:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_data

            # Determine which mock data to return
            if endpoint == "metrics":
                data = MOCK_METRICS
            else:
                data = ENDPOINT_DATA.get(endpoint, {
                    "message": f"No data available for endpoint {endpoint}",
                    "status": "error"
                })

            # Cache the response if cache_key provided
            if cache_key:
                cache.set(cache_key, data, timeout)
                logger.debug(f"Cached data for {cache_key}")

            return data

        except Exception as e:
            logger.error(f"Error fetching data for endpoint {endpoint}: {str(e)}")
            return {
                "message": "Error fetching data",
                "status": "error",
                "error": str(e)
            }

    def fetch_metrics(self) -> Dict[str, Any]:
        """Fetch all metrics with error handling"""
        try:
            return self._get_cached("metrics", cache_key="metrics_cache")
        except Exception as e:
            logger.error(f"Error fetching metrics: {str(e)}")
            return {
                "message": "Error fetching metrics",
                "status": "error",
                "error": str(e)
            }
