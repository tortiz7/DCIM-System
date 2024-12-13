from django.urls import path
from django.shortcuts import redirect
from .views import ChatbotView, MetricsView, health_check

def root_redirect(request):
    return redirect('chat')

urlpatterns = [
    path('', root_redirect, name='root'),
    path('chat/', ChatbotView.as_view(), name='chat'),
    path('metrics/', MetricsView.as_view(), name='prometheus-metrics'),
    path('health/', health_check, name='health-check'),
]
