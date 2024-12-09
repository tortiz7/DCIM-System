from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum

from ralph.api import RalphAPIViewSet, router
from ralph.assets.models import DataCenterAsset, BackOfficeAsset
from ralph.networks.models import Network, IPAddress

class AssetMetricsViewSet(RalphAPIViewSet):
    """
    Viewset for aggregated asset metrics
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

    @action(detail=False, methods=['get'])
    def network(self, request):
        """Get network metrics"""
        network_queryset = Network.objects.all()
        ip_queryset = IPAddress.objects.all()
        return Response({
            'total_networks': network_queryset.count(),
            'ip_usage': {
                'total': ip_queryset.count(),
                'used': ip_queryset.filter(status='used').count(),
                'reserved': ip_queryset.filter(
                    status='reserved'
                ).count()
            }
        })