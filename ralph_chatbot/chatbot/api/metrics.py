from typing import Dict, Any
import logging
from django.conf import settings
from .client import RalphAPIClient

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
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

        for metric_type, keywords in keyword_mapping.items():
            if any(word in question.lower() for word in keywords):
                metrics.update(getattr(self, f'get_{metric_type}')())

        if not metrics:
            metrics = self.client.fetch_metrics()

        return metrics or {"message": "No metrics available"}

    def get_asset_metrics(self) -> Dict[str, Any]:
        try:
            dc_metrics = self.client._get_cached('assets/metrics/datacenter/', 'dc_asset_metrics')
            bo_metrics = self.client._get_cached('assets/metrics/backoffice/', 'bo_asset_metrics')
            return {"assets": {"datacenter": dc_metrics, "backoffice": bo_metrics}}
        except Exception as e:
            logger.error(f"Error fetching asset metrics: {e}")
            return {"assets": "Error fetching asset metrics"}

    def get_network_metrics(self) -> Dict[str, Any]:
        try:
            return {"networks": self.client._get_cached('metrics/network_metrics/', 'network_metrics')}
        except Exception as e:
            logger.error(f"Error fetching network metrics: {e}")
            return {"networks": "Error fetching network metrics"}

    def get_power_metrics(self) -> Dict[str, Any]:
        try:
            return {"power": self.client._get_cached('metrics/power_metrics/', 'power_metrics')}
        except Exception as e:
            logger.error(f"Error fetching power metrics: {e}")
            return {"power": "Error fetching power metrics"}

    def get_rack_metrics(self) -> Dict[str, Any]:
        try:
            return {"racks": self.client._get_cached('metrics/rack_metrics/', 'rack_metrics')}
        except Exception as e:
            logger.error(f"Error fetching rack metrics: {e}")
            return {"racks": "Error fetching rack metrics"}

    def get_deployment_metrics(self) -> Dict[str, Any]:
        try:
            return {"deployments": self.client._get_cached('metrics/deployment_metrics/', 'deployment_metrics')}
        except Exception as e:
            logger.error(f"Error fetching deployment metrics: {e}")
            return {"deployments": "Error fetching deployment metrics"}

    def get_all_metrics(self) -> Dict[str, Any]:
        try:
            return self.client.fetch_metrics()
        except Exception as e:
            logger.error(f"Error fetching all metrics: {e}")
            return {"message": "Error fetching all metrics"}

    def refresh_cache(self) -> None:
        try:
            self.get_asset_metrics()
            self.get_network_metrics()
            self.get_power_metrics()
            self.get_rack_metrics()
            self.get_deployment_metrics()
            logger.info("Successfully refreshed all metrics caches")
        except Exception as e:
            logger.error(f"Error refreshing metrics cache: {e}")
