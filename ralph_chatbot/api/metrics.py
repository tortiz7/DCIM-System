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
        """Get relevant metrics based on the question context"""
        metrics = {}
        
        # Determine which metrics to fetch based on question keywords
        if any(word in question.lower() for word in ['asset', 'server', 'hardware']):
            metrics.update(self.get_asset_metrics())
        
        if any(word in question.lower() for word in ['network', 'ip', 'connection']):
            metrics.update(self.get_network_metrics())
            
        if any(word in question.lower() for word in ['power', 'energy', 'consumption']):
            metrics.update(self.get_power_metrics())
            
        return metrics

    def get_asset_metrics(self) -> Dict[str, Any]:
        """Get asset-related metrics"""
        try:
            return {
                'datacenter_assets': self.client.get_datacenter_metrics(),
                'backoffice_assets': self.client.get_backoffice_metrics()
            }
        except Exception as e:
            logger.error(f"Error fetching asset metrics: {e}")
            return {}

    def get_network_metrics(self) -> Dict[str, Any]:
        """Get network-related metrics"""
        try:
            return {
                'networks': self.client.get_network_metrics()
            }
        except Exception as e:
            logger.error(f"Error fetching network metrics: {e}")
            return {}

    def get_power_metrics(self) -> Dict[str, Any]:
        """Get power consumption metrics"""
        try:
            return {
                'power': self.client.get_power_metrics()
            }
        except Exception as e:
            logger.error(f"Error fetching power metrics: {e}")
            return {}

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available metrics"""
        return {
            'assets': self.get_asset_metrics(),
            'networks': self.get_network_metrics(),
            'power': self.get_power_metrics()
        }