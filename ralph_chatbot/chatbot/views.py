from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .api.client import RalphAPIClient
from .api.metrics import MetricsCollector
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class ChatbotView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(settings.MODEL_PATH)
        self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_PATH)
        self.api_client = RalphAPIClient(
            base_url=settings.RALPH_API_URL,
            token=settings.RALPH_API_TOKEN
        )
        self.metrics_collector = MetricsCollector()

    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response(
                {'error': 'Question is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Gather relevant metrics based on question context
        metrics = self.metrics_collector.get_relevant_metrics(question)
        
        # Generate response
        inputs = self.tokenizer(
            question,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        )
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return Response({
            'response': response,
            'metrics': metrics
        })

class MetricsView(APIView):
    def get(self, request):
        collector = MetricsCollector()
        metrics = collector.get_all_metrics()
        return Response(metrics)