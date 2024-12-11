from typing import Dict, Any
import logging
from django.conf import settings
from .client import RalphAPIClient

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        # Use mocked RalphAPIClient
        self.client = RalphAPIClient(
            base_url=settings.RALPH_API_URL,
            token=settings.RALPH_API_TOKEN
        )

    def get_relevant_metrics(self, question: str) -> Dict[str, Any]:
        metrics = {}
        keyword_mapping = {
            'asset_metrics': ['asset', 'server', 'hardware', 'device', 'equipment'],
            'network_metrics': ['network', 'ip', 'connection', 'bandwidth', 'dns'],
            'power_metrics': ['power', 'energy', 'consumption', 'watts', 'pdu'],
            'rack_metrics': ['rack', 'cooling', 'temperature', 'space', 'capacity'],
            'deployment_metrics': ['deployment', 'provision', 'install', 'setup']
        }

        # If question matches any keywords, fetch that category's metrics
        for metric_type, keywords in keyword_mapping.items():
            if any(word in question.lower() for word in keywords):
                metrics.update(getattr(self, f'get_{metric_type}')())

        # If no keywords matched, return a subset of all metrics
        if not metrics:
            # Return a portion of the overall metrics if no keywords matched
            overall = self.client.fetch_metrics()
            metrics.update(overall)

        return metrics

    def get_asset_metrics(self) -> Dict[str, Any]:
        try:
            dc_metrics = self.client._get_cached(
                'assets/metrics/datacenter/',
                cache_key='dc_asset_metrics'
            )
            bo_metrics = self.client._get_cached(
                'assets/metrics/backoffice/',
                cache_key='bo_asset_metrics'
            )

            # Combine data in a single dict
            return {
                "assets": {
                    "datacenter": dc_metrics,
                    "backoffice": bo_metrics
                }
            }
        except Exception as e:
            logger.error(f"Error fetching asset metrics: {e}")
            return {}

    def get_network_metrics(self) -> Dict[str, Any]:
        try:
            data = self.client._get_cached('metrics/network_metrics/', cache_key='network_metrics')
            return {"networks": data}
        except Exception as e:
            logger.error(f"Error fetching network metrics: {e}")
            return {}

    def get_power_metrics(self) -> Dict[str, Any]:
        try:
            data = self.client._get_cached('metrics/power_metrics/', cache_key='power_metrics')
            return {"power": data}
        except Exception as e:
            logger.error(f"Error fetching power metrics: {e}")
            return {}

    def get_rack_metrics(self) -> Dict[str, Any]:
        try:
            data = self.client._get_cached('metrics/rack_metrics/', cache_key='rack_metrics')
            return {"racks": data}
        except Exception as e:
            logger.error(f"Error fetching rack metrics: {e}")
            return {}

    def get_deployment_metrics(self) -> Dict[str, Any]:
        try:
            data = self.client._get_cached('metrics/deployment_metrics/', cache_key='deployment_metrics')
            return {"deployments": data}
        except Exception as e:
            logger.error(f"Error fetching deployment metrics: {e}")
            return {}

    def get_all_metrics(self) -> Dict[str, Any]:
        # Return all mocked metrics from 'metrics' endpoint
        try:
            return self.client.fetch_metrics()
        except Exception as e:
            logger.error(f"Error fetching all metrics: {e}")
            return {}

    def refresh_cache(self) -> None:
        try:
            # Just call each metric fetch method to refresh cache
            self.get_asset_metrics()
            self.get_network_metrics()
            self.get_power_metrics()
            self.get_rack_metrics()
            self.get_deployment_metrics()
            logger.info("Successfully refreshed all metrics caches")
        except Exception as e:
            logger.error(f"Error refreshing metrics cache: {e}")
