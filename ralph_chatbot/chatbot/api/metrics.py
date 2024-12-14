from typing import Dict, Any
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Metrics collector using mock metrics for demonstration purposes."""

    def __init__(self):
        self.cache_timeout = getattr(settings, 'METRICS_CACHE_TIMEOUT', 300)

    def get_relevant_metrics(self, query: str) -> Dict[str, Any]:
        """Get metrics relevant to the query with keyword matching."""
        try:
            metrics = {}
            keyword_mapping = {
                'asset_metrics': ['asset', 'server', 'hardware', 'device', 'equipment'],
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
        """Get mock asset metrics."""
        try:
            cache_key = 'asset_metrics'
            cached_metrics = cache.get(cache_key)

            if cached_metrics:
                return cached_metrics

            # Fetch mock metrics from settings
            metrics = settings.MOCK_ASSET_METRICS

            cache.set(cache_key, metrics, self.cache_timeout)
            return metrics

        except Exception as e:
            logger.error(f"Error fetching asset metrics: {e}")
            return {"assets": "Error fetching asset metrics"}

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all mock metrics."""
        try:
            return self.get_asset_metrics()
        except Exception as e:
            logger.error(f"Error fetching all metrics: {e}")
            return {"message": "Error fetching all metrics"}

    def refresh_cache(self) -> None:
        """Refresh all metric caches."""
        try:
            cache.delete_many(['asset_metrics'])
            self.get_asset_metrics()
            logger.info("Successfully refreshed all metrics caches")
        except Exception as e:
            logger.error(f"Error refreshing metrics cache: {e}")
