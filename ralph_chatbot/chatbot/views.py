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
from .api.client import RalphAPIClient
import json

logger = logging.getLogger(__name__)

class ChatbotView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = RalphAPIClient()
        self.initialize_model()

    def initialize_model(self):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                trust_remote_code=True
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            self.model = PeftModel.from_pretrained(
                base_model,
                "ralph_lora_adapters",
                torch_dtype=torch.float16,
                device_map="auto"
            )
            self.model.eval()
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    def generate_response(self, question, metrics=None):
        try:
            if metrics:
                context = f"""Current System Status:
                Assets: {metrics['assets']['total_count']} total
                Network: {metrics['networks']['status']}
                Power Usage: {metrics['power']['total_consumption']}kW
                
                Question: {question}
                """
            else:
                context = question

            inputs = self.tokenizer(
                context,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id
                )

            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response.split("Question: ")[-1].split("Answer: ")[-1].strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error generating a response. Please try again."

    def get(self, request):
        return render(request, 'chatbot/chat_widget.html')

    def post(self, request):
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            metrics = self.client.fetch_metrics()
            response = self.generate_response(question, metrics)
            return JsonResponse({
                'response': response,
                'metrics': metrics
            })
        except Exception as e:
            logger.error(f"Error in post request: {e}")
            return JsonResponse({'error': str(e)}, status=500)


class MetricsView(APIView):
    def get(self, request):
        return Response({
            'status': 'OK',
            'metrics': {'model_loaded': True}
        })


def health_check(request):
    return HttpResponse("healthy", status=200)
