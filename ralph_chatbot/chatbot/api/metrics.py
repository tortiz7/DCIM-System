from typing import Dict, Any, List
import logging
from django.conf import settings
from django.core.cache import cache
from .client import RalphAPIClient

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Enhanced metrics collector with better error handling and caching"""
    
    def __init__(self):
        self.client = RalphAPIClient(
            base_url=settings.RALPH_API_URL,
            token=settings.RALPH_API_TOKEN
        )
        self.cache_timeout = getattr(settings, 'METRICS_CACHE_TIMEOUT', 300)

    def get_relevant_metrics(self, query: str) -> Dict[str, Any]:
        """Get metrics relevant to the query with enhanced keyword matching"""
        try:
            metrics = {}
            keyword_mapping = {
                'asset_metrics': [
                    'asset', 'server', 'hardware', 'device', 'equipment',
                    'datacenter', 'inventory'
                ],
                'network_metrics': [
                    'network', 'ip', 'connection', 'bandwidth', 'dns',
                    'vlan', 'subnet', 'routing'
                ],
                'power_metrics': [
                    'power', 'energy', 'consumption', 'watts', 'pdu',
                    'electricity', 'usage'
                ],
                'rack_metrics': [
                    'rack', 'cooling', 'temperature', 'space', 'capacity',
                    'unit', 'mounting'
                ],
                'deployment_metrics': [
                    'deployment', 'provision', 'install', 'setup',
                    'automation', 'configuration'
                ]
            }

            query_terms = query.lower().split()
            
            for metric_type, keywords in keyword_mapping.items():
                if any(term in keywords for term in query_terms):
                    metric_method = getattr(self, f'get_{metric_type}')
                    metrics.update(metric_method())

            if not metrics:
                metrics = self.get_all_metrics()

            return metrics or {"message": "No relevant metrics available"}

        except Exception as e:
            logger.error(f"Error getting relevant metrics: {e}")
            return {
                "message": "Error retrieving metrics",
                "status": "error",
                "error": str(e)
            }

    def get_asset_metrics(self) -> Dict[str, Any]:
        """Get asset metrics with enhanced error handling"""
        try:
            cache_key = 'asset_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            dc_metrics = self.client._get_cached(
                'assets/metrics/datacenter/',
                'dc_asset_metrics'
            )
            bo_metrics = self.client._get_cached(
                'assets/metrics/backoffice/',
                'bo_asset_metrics'
            )
            
            metrics = {
                "assets": {
                    "datacenter": dc_metrics,
                    "backoffice": bo_metrics,
                    "total": {
                        "count": dc_metrics.get('datacenter_assets', 0) + 
                                bo_metrics.get('backoffice_assets', 0)
                    }
                }
            }
            
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching asset metrics: {e}")
            return {"assets": "Error fetching asset metrics"}

    def get_network_metrics(self) -> Dict[str, Any]:
        """Get network metrics with caching"""
        try:
            cache_key = 'network_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            metrics = {
                "networks": self.client._get_cached(
                    'metrics/network_metrics/',
                    'network_metrics'
                )
            }
            
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching network metrics: {e}")
            return {"networks": "Error fetching network metrics"}

    def get_power_metrics(self) -> Dict[str, Any]:
        """Get power metrics with caching"""
        try:
            cache_key = 'power_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            metrics = {
                "power": self.client._get_cached(
                    'metrics/power_metrics/',
                    'power_metrics'
                )
            }
            
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching power metrics: {e}")
            return {"power": "Error fetching power metrics"}

    def get_rack_metrics(self) -> Dict[str, Any]:
        """Get rack metrics with caching"""
        try:
            cache_key = 'rack_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            metrics = {
                "racks": self.client._get_cached(
                    'metrics/rack_metrics/',
                    'rack_metrics'
                )
            }
            
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching rack metrics: {e}")
            return {"racks": "Error fetching rack metrics"}

    def get_deployment_metrics(self) -> Dict[str, Any]:
        """Get deployment metrics with caching"""
        try:
            cache_key = 'deployment_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            metrics = {
                "deployments": self.client._get_cached(
                    'metrics/deployment_metrics/',
                    'deployment_metrics'
                )
            }
            
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching deployment metrics: {e}")
            return {"deployments": "Error fetching deployment metrics"}

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics with caching"""
        try:
            cache_key = 'all_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics

            metrics = self.client.fetch_metrics()
            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching all metrics: {e}")
            return {"message": "Error fetching all metrics"}

    def refresh_cache(self) -> None:
        """Refresh all metric caches"""
        try:
            cache.delete_many([
                'asset_metrics',
                'network_metrics',
                'power_metrics',
                'rack_metrics',
                'deployment_metrics',
                'all_metrics'
            ])
            
            self.get_asset_metrics()
            self.get_network_metrics()
            self.get_power_metrics()
            self.get_rack_metrics()
            self.get_deployment_metrics()
            
            logger.info("Successfully refreshed all metrics caches")
        except Exception as e:
            logger.error(f"Error refreshing metrics cache: {e}")