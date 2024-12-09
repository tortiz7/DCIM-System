from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from ralph.assets.models import Asset
from ralph.data_center.models import DataCenterAsset
from ralph.back_office.models import BackOfficeAsset
from ralph.networks.models import Network, IPAddress
from ralph.deployment.models import Deployment
from ralph.dc_view.models_assets import Rack

class MetricsViewSet(viewsets.ViewSet):
    """
    API endpoints for Ralph system-wide metrics
    """
    
    @action(detail=False, methods=['get'])
    def asset_metrics(self, request):
        """Get asset counts and statuses"""
        return Response({
            'total_assets': Asset.objects.count(),
            'datacenter_assets': {
                'total': DataCenterAsset.objects.count(),
                'by_status': dict(DataCenterAsset.objects.values_list(
                    'status'
                ).annotate(count=Count('id')))
            },
            'backoffice_assets': {
                'total': BackOfficeAsset.objects.count(),
                'by_status': dict(BackOfficeAsset.objects.values_list(
                    'status'
                ).annotate(count=Count('id')))
            }
        })

    @action(detail=False, methods=['get'])
    def power_metrics(self, request):
        """Get power consumption metrics"""
        assets = DataCenterAsset.objects.filter(power_consumption__gt=0)
        return Response({
            'total_power': sum(a.power_consumption for a in assets),
            'by_rack': dict(
                assets.values_list('rack__name').annotate(
                    power=Sum('power_consumption')
                )
            ),
            'peak_consumers': assets.order_by('-power_consumption')[:5].values(
                'hostname', 'power_consumption'
            )
        })

    @action(detail=False, methods=['get'])
    def network_metrics(self, request):
        """Get network utilization metrics"""
        return Response({
            'total_networks': Network.objects.count(),
            'ip_addresses': {
                'total': IPAddress.objects.count(),
                'used': IPAddress.objects.filter(status='used').count()
            },
            'network_capacity': {
                str(net): net.get_ip_usage_count()
                for net in Network.objects.all()
            }
        })

    @action(detail=False, methods=['get'])
    def deployment_metrics(self, request):
        """Get deployment status metrics"""
        return Response({
            'total_deployments': Deployment.objects.count(),
            'active_deployments': Deployment.objects.filter(
                is_active=True
            ).count(),
            'recent_deployments': list(Deployment.objects.order_by(
                '-created'
            )[:5].values('id', 'status', 'created'))
        })

    @action(detail=False, methods=['get'])
    def rack_metrics(self, request):
        """Get rack space and cooling metrics"""
        racks = Rack.objects.all()
        return Response({
            'rack_utilization': {
                str(rack): {
                    'capacity': rack.get_capacity(),
                    'free_u': rack.get_free_u(),
                    'temperature': rack.get_temperature()
                } for rack in racks
            }
        })