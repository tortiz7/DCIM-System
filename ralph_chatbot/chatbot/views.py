from django.views import View
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import logging
import json
from django.conf import settings
from .api.client import RalphAPIClient
from .api.metrics import MetricsCollector
import threading
import os

logger = logging.getLogger(__name__)

class ChatbotView(View):
    _model_initialized = False
    _model_lock = threading.Lock()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = RalphAPIClient()
        self.metrics_collector = MetricsCollector()
        self.model = None
        self.tokenizer = None
        self._ensure_model_initialized()

    def _ensure_model_initialized(self):
        if not ChatbotView._model_initialized:
            # Start model initialization in a background thread
            init_thread = threading.Thread(target=self.initialize_model, daemon=True)
            init_thread.start()


    def initialize_model(self):
        if ChatbotView._model_initialized:
            return

        with ChatbotView._model_lock:
            if ChatbotView._model_initialized:
                return

            try:
                logger.info("Starting model initialization...")
                base_path = settings.MODEL_PATH['base_path']
                adapters_path = settings.MODEL_PATH['adapters_path']

                if not os.path.exists(base_path):
                    raise ValueError(f"Base model path not found: {base_path}")
                if not os.path.exists(adapters_path):
                    raise ValueError(f"Adapters path not found: {adapters_path}")

                # Configure 4-bit quantization
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

                logger.info(f"Loading tokenizer from {base_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    base_path,
                    trust_remote_code=True,
                    use_fast=False
                )

                logger.info(f"Loading base model from {base_path}")
                base_model = AutoModelForCausalLM.from_pretrained(
                    base_path,
                    quantization_config=quantization_config,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    use_cache=True
                )

                logger.info(f"Loading LoRA adapters from {adapters_path}")
                self.model = PeftModel.from_pretrained(
                    base_model,
                    adapters_path,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )

                self.model.eval()
                ChatbotView._model_initialized = True
                logger.info("Model initialization completed successfully")

            except Exception as e:
                logger.error(f"Error initializing model: {e}", exc_info=True)
                self.model = None
                self.tokenizer = None

    def generate_response(self, question, metrics=None):
        if self.model is None or self.tokenizer is None:
            return "Model not initialized properly."

        prompt = ("You are Ralph Assistant, an expert in Ralph DCIM and asset management.\n"
                  "Please answer the user's questions using the given system metrics when relevant.\n\n")
        if metrics:
            prompt += f"System Metrics:\nAssets: {metrics['assets']['total_count']} total, {metrics['assets']['status_summary']}\n"
            prompt += f"Network: {metrics['networks']['status']}\nPower: {metrics['power']['total_consumption']} kW\n\n"
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
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I encountered an error generating the response."

    def get(self, request):
        # Render the chat widget template
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
            'metrics': {'model_loaded': ChatbotView._model_initialized}
        })


def health_check(request):
    if torch.cuda.is_available() and ChatbotView._model_initialized:
        return HttpResponse("healthy", status=200)
    return HttpResponse("unhealthy", status=503)
