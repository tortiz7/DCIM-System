from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import logging
import json
from django.conf import settings
from .api.client import RalphAPIClient
from .api.metrics import MetricsCollector

logger = logging.getLogger(__name__)

class ChatbotView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = RalphAPIClient()
        self.metrics_collector = MetricsCollector()
        self.model = None
        self.tokenizer = None
        self.initialize_model()

    def initialize_model(self):
        try:
            base_path = settings.MODEL_PATH['base_path']
            adapters_path = settings.MODEL_PATH['adapters_path']

            # Load tokenizer with no fast tokenization
            self.tokenizer = AutoTokenizer.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                trust_remote_code=True,
                use_fast=False
            )

            base_model = AutoModelForCausalLM.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

            # Load LoRA adapters
            self.model = PeftModel.from_pretrained(
                base_model,
                adapters_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )

            self.model.eval()
            logger.info("Model and LoRA adapter loaded successfully.")
        except Exception as e:
            logger.error(f"Error initializing model: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None

    def generate_response(self, question, metrics=None):
        if self.model is None or self.tokenizer is None:
            return "Model not initialized properly."

        # Create a prompt that includes metrics if available
        prompt = "You are Ralph Assistant, an expert in Ralph DCIM and asset management.\n"
        if metrics:
            prompt += f"System Metrics:\nAssets: {metrics['assets']['total_count']} total, {metrics['assets']['status_summary']}\nNetwork: {metrics['networks']['status']}\nPower: {metrics['power']['total_consumption']} kW\n\n"
        prompt += f"Question: {question}\nAnswer:"

        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.95,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract the answer part
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I encountered an error generating the response."

    def get(self, request):
        return render(request, 'chat_widget.html')

    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            question = data.get('question', '')
            metrics = self.metrics_collector.get_all_metrics()
            response = self.generate_response(question, metrics)
            return JsonResponse({
                'response': response,
                'metrics': metrics
            })
        except Exception as e:
            logger.error(f"Error in POST request: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


class MetricsView(APIView):
    def get(self, request):
        return Response({
            'status': 'OK',
            'metrics': {'model_loaded': True}
        })


def health_check(request):
    # Simple health check
    if torch.cuda.is_available() and True:  # Add any other checks here
        return HttpResponse("healthy", status=200)
    return HttpResponse("unhealthy", status=503)
