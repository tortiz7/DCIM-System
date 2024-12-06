from django.urls import path
from .views import ChatbotView, MetricsView

urlpatterns = [
    path('chat/', ChatbotView.as_view(), name='chat'),
    path('metrics/', MetricsView.as_view(), name='prometheus-metrics'),
    path('health/', health_check, name='health-check'),
]