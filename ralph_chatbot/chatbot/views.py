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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .api.client import RalphAPIClient
from .api.metrics import MetricsCollector
import threading
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')  # Keep CSRF exempt since we removed CSRF
class ChatbotView(View):
    _model_initialized = False
    _model_lock = threading.Lock()
    _model = None
    _tokenizer = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = RalphAPIClient()
        self.metrics_collector = MetricsCollector()
        self._ensure_model_initialized()

    def _ensure_model_initialized(self):
        if not ChatbotView._model_initialized:
            # Initialize synchronously instead of in a thread to ensure it's ready
            self.initialize_model()

    def verify_model_files(self):
        base_path = settings.MODEL_PATH['base_path']
        adapters_path = settings.MODEL_PATH['adapters_path']

        required_files = {
            'base': ['tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json'],
            'adapters': ['adapter_config.json', 'adapter_model.safetensors']
        }

        logger.info(f"Verifying model files in {base_path}")
        for file in required_files['base']:
            file_path = Path(base_path) / file
            if not file_path.exists():
                logger.error(f"Missing required file: {file_path}")
                return False

        logger.info(f"Verifying adapter files in {adapters_path}")
        for file in required_files['adapters']:
            file_path = Path(adapters_path) / file
            if not file_path.exists():
                logger.error(f"Missing required file: {file_path}")
                return False

        return True

    def initialize_model(self):
        if ChatbotView._model_initialized:
            return

        with ChatbotView._model_lock:
            if ChatbotView._model_initialized:
                return

            try:
                logger.info("Starting model initialization...")

                # Verify all required files exist
                if not self.verify_model_files():
                    raise ValueError("Missing required model files")

                base_path = settings.MODEL_PATH['base_path']
                adapters_path = settings.MODEL_PATH['adapters_path']

                logger.info(f"Using paths: base={base_path}, adapters={adapters_path}")
                logger.info(f"CUDA available: {torch.cuda.is_available()}")
                if torch.cuda.is_available():
                    logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")

                # Configure 4-bit quantization
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )

                logger.info(f"Loading tokenizer from {base_path}")
                ChatbotView._tokenizer = AutoTokenizer.from_pretrained(
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
                ChatbotView._model = PeftModel.from_pretrained(
                    base_model,
                    adapters_path,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )

                ChatbotView._model.eval()
                ChatbotView._model_initialized = True
                logger.info("Model initialization completed successfully")

            except Exception as e:
                logger.error(f"Error initializing model: {e}", exc_info=True)
                ChatbotView._model = None
                ChatbotView._tokenizer = None

    def generate_response(self, question, metrics=None):
        if not ChatbotView._model_initialized or ChatbotView._model is None or ChatbotView._tokenizer is None:
            return "Model initialization in progress. Please try again in a moment."

        generation_config = {
            'max_new_tokens': 200,
            'temperature': 0.7,
            'do_sample': True,
            'top_p': 0.95,
            'repetition_penalty': 1.2
        }

        prompt = ("You are Ralph Assistant, an expert in Ralph DCIM and asset management.\n"
                  "Please answer the user's questions using the given system metrics when relevant.\n\n")
        if metrics:
            prompt += f"System Metrics:\nAssets: {metrics.get('assets', {}).get('total_count', 'N/A')}\n"
        prompt += f"Question: {question}\nAnswer:"

        try:
            inputs = ChatbotView._tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(ChatbotView._model.device)

            with torch.no_grad():
                outputs = ChatbotView._model.generate(
                    **inputs,
                    max_new_tokens=generation_config.get('max_new_tokens', 200),
                    temperature=generation_config.get('temperature', 0.7),
                    do_sample=generation_config.get('do_sample', True),
                    top_p=generation_config.get('top_p', 0.95),
                    repetition_penalty=generation_config.get('repetition_penalty', 1.2),
                    pad_token_id=ChatbotView._tokenizer.eos_token_id
                )

            response = ChatbotView._tokenizer.decode(outputs[0], skip_special_tokens=True)
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I encountered an error generating the response. Please try again."

    def get(self, request):
        return render(request, 'chat_widget.html')

    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
            question = data.get('question', '').strip()

            if not question:
                return JsonResponse({'error': 'No question provided'}, status=400)

            metrics = self.metrics_collector.get_all_metrics()
            response = self.generate_response(question, metrics)

            return JsonResponse({
                'response': response,
                'status': 'success'
            })
        except Exception as e:
            logger.error(f"Error in POST request: {e}", exc_info=True)
            return JsonResponse({
                'response': 'I apologize, but I am having trouble processing your request. Please try again.',
                'status': 'error'
            })


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
