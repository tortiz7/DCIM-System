from typing import Dict, Any
import requests
import logging
from django.core.cache import cache
from functools import lru_cache

logger = logging.getLogger(__name__)

class RalphAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Token {token}',
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_cached(self, endpoint: str, cache_key: str = None, timeout: int = 300) -> Dict[str, Any]:
        """Make a GET request with caching"""
        if not cache_key:
            cache_key = f'ralph_api_{endpoint}'
            
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        response = self.session.get(f'{self.base_url}/{endpoint}')
        response.raise_for_status()
        data = response.json()
        
        cache.set(cache_key, data, timeout)
        return data

    def get_datacenter_metrics(self) -> Dict[str, Any]:
        """Get data center asset metrics"""
        return self._get_cached('datacenter-assets/')

    def get_backoffice_metrics(self) -> Dict[str, Any]:
        """Get back office asset metrics"""
        return self._get_cached('backoffice-assets/')

    def get_network_metrics(self) -> Dict[str, Any]:
        """Get network infrastructure metrics"""
        return self._get_cached('networks/')

    def get_power_metrics(self) -> Dict[str, Any]:
        """Get power consumption metrics"""
        return self._get_cached('power-metrics/')

    @lru_cache(maxsize=128)
    def get_asset_details(self, asset_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific asset"""
        return self._get_cached(f'assets/{asset_id}/')