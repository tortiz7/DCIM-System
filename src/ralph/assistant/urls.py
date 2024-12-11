from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='assistant-chat'),
    path('metrics/', views.MetricsView.as_view(), name='assistant-metrics'),
    path('widget/', views.AssistantWidgetView.as_view(), name='assistant-widget'),
]