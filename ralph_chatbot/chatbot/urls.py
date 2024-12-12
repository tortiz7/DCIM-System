from django.urls import path
from django.views.generic import TemplateView
from django.shortcuts import redirect
from .views import ChatbotView, MetricsView, health_check

def root_redirect(request):
    return redirect('chat')

urlpatterns = [
    # Root URL handler
    path('', root_redirect, name='root'),  # Redirects to /chat/
    
    # Existing paths
    path('chat/', ChatbotView.as_view(), name='chat'),
    path('metrics/', MetricsView.as_view(), name='prometheus-metrics'),
    path('health/', health_check, name='health-check'),
]