import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.conf import settings
from ralph.data_center.models import DataCenterAsset
from ralph.back_office.models import BackOfficeAsset
from ralph.assets.models.assets import Asset
from ralph.licences.models import Licence
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class ChatView(APIView):
    def post(self, request):
        message = request.data.get('message')
        # Using 'question' if chatbot expects 'question', otherwise use 'message'.
        response = requests.post(
            'http://chatbot:8001/chat/',
            json={'question': message}
        )
        return Response(response.json())

class MetricsView(APIView):
    def get(self, request):
        metrics = {
            'assets': {
                'total': Asset.objects.count(),
                'datacenter': DataCenterAsset.objects.count(),
                'backoffice': BackOfficeAsset.objects.count(),
                'licences': Licence.objects.count(),
            },
            'status': {
                'in_use': Asset.objects.filter(status='in_use').count(),
                'free': Asset.objects.filter(status='free').count(),
                'damaged': Asset.objects.filter(status='damaged').count(),
            }
        }
        return Response(metrics)

class AssistantWidgetView(TemplateView):
    template_name = 'assistant/widget.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chatbot_url'] = settings.CHATBOT_URL
        return context
