from from django.urls import re_path as url

from ralph.dashboards.views import DashboardView

urlpatterns = [
    url(
        r'^dashboard_view/(?P<dashboard_id>\d+)/$',
        DashboardView.as_view(),
        name='dashboard_view'
    ),
]
