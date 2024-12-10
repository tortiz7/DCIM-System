from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum

from ralph.api import RalphAPIViewSet
from ralph.assets.models import DataCenterAsset, BackOfficeAsset
from ralph.networks.models import Network, IPAddress

class AssetMetricsViewSet(RalphAPIViewSet):
    """
    Viewset for aggregated asset and infrastructure metrics.
    """

    @action(detail=False, methods=['get'])
    def datacenter(self, request):
        """Get data center asset metrics"""
        queryset = DataCenterAsset.objects.all()
        return Response({
            'total': queryset.count(),
            'by_status': dict(
                queryset.values_list('status')
                .annotate(count=Count('id'))
            ),
            'power_consumption': {
                'total': queryset.aggregate(
                    total=Sum('power_consumption')
                )['total'],
                'by_rack': dict(
                    queryset.values('rack__name')
                    .annotate(power=Sum('power_consumption'))
                )
            }
        })

    @action(detail=False, methods=['get'])
    def backoffice(self, request):
        """Get back office asset metrics"""
        queryset = BackOfficeAsset.objects.all()
        return Response({
            'total': queryset.count(),
            'by_status': dict(
                queryset.values_list('status')
                .annotate(count=Count('id'))
            ),
            'by_user': dict(
                queryset.values('user__username')
                .annotate(count=Count('id'))
            )
        })

    # Previously we had 'network', but chatbot expects 'network_metrics'
    @action(detail=False, methods=['get'], url_path='network_metrics')
    def network_metrics(self, request):
        """Get network-related metrics"""
        network_queryset = Network.objects.all()
        ip_queryset = IPAddress.objects.all()
        return Response({
            'total_networks': network_queryset.count(),
            'ip_usage': {
                'total': ip_queryset.count(),
                'used': ip_queryset.filter(status='used').count(),
                'reserved': ip_queryset.filter(status='reserved').count()
            }
        })

    @action(detail=False, methods=['get'], url_path='power_metrics')
    def power_metrics(self, request):
        """Get power consumption metrics - dummy data for now"""
        # Ideally, implement real logic here
        return Response({
            'total_power_consumption_kw': 1234,  # dummy value
            'average_power_per_asset_w': 220      # dummy value
        })

    @action(detail=False, methods=['get'], url_path='rack_metrics')
    def rack_metrics(self, request):
        """Get rack space and cooling metrics - dummy data"""
        # Implement real logic if available
        return Response({
            'total_racks': 50,  # dummy
            'average_rack_usage_percent': 75.3  # dummy
        })

    @action(detail=False, methods=['get'], url_path='deployment_metrics')
    def deployment_metrics(self, request):
        """Get deployment status metrics - dummy data"""
        # Implement real logic if available
        return Response({
            'total_deployments': 200,    # dummy
            'successful_deployments': 190,
            'failed_deployments': 10
        })
