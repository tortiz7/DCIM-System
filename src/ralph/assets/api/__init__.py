from django.utils.translation import ugettext_lazy as _

from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.metrics import AssetMetricsViewSet
from ralph.assets.models import (
    AssetModel, Category, Environment, Service, 
    ServiceEnvironment
)

# Import all necessary viewsets for metrics to work
from .viewsets.service_environment import ServiceEnvironmentViewSet
from .viewsets.service import ServiceViewSet

# Register all endpoints
router.register(
    r'assets/metrics',
    AssetMetricsViewSet,
    basename='asset-metrics'
)

# We need these base registrations for the metrics API to work properly
router.register(r'services', ServiceViewSet)
router.register(r'service-environments', ServiceEnvironmentViewSet)