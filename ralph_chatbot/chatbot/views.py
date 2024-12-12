from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import HttpResponse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import logging
import os

logger = logging.getLogger(__name__)

class ChatbotView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Configure quantization
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # Verify model paths exist
            if not os.path.exists(settings.MODEL_PATH['base_path']):
                raise ValueError(f"Model base path does not exist: {settings.MODEL_PATH['base_path']}")
            if not os.path.exists(settings.MODEL_PATH['adapters_path']):
                raise ValueError(f"Adapters path does not exist: {settings.MODEL_PATH['adapters_path']}")

            # Load base model with proper configuration
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.MODEL_PATH['base_path'],
                device_map="auto",
                torch_dtype=torch.float16,
                quantization_config=bnb_config,
                rope_scaling={
                    "name": "dynamic",
                    "factor": 2.0
                }
            )

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.MODEL_PATH['base_path'],
                trust_remote_code=True
            )

            # Load adapter model
            if os.path.exists(os.path.join(settings.MODEL_PATH['adapters_path'], 'adapter_config.json')):
                self.model = PeftModel.from_pretrained(
                    self.model, 
                    settings.MODEL_PATH['adapters_path']
                )
                logger.info("LoRA adapter loaded successfully")
            else:
                logger.warning("No LoRA adapter found, using base model only")

            logger.info("Model initialization completed successfully")

        except Exception as e:
            logger.error(f"Error initializing ChatbotView: {str(e)}", exc_info=True)
            # Don't raise the exception - allow the view to initialize but log the error
            self.model = None
            self.tokenizer = None

    def post(self, request):
        if self.model is None or self.tokenizer is None:
            return Response(
                {'error': 'Model not properly initialized'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        question = request.data.get('question')
        if not question:
            return Response(
                {'error': 'Question is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            inputs = self.tokenizer(
                question,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=200,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.95,
                    repetition_penalty=1.2
                )
            
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return Response({
                'response': response_text,
                'metrics': {'status': 'success'}
            })
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Error generating response'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MetricsView(APIView):
    def get(self, request):
        # Implementation for metrics
        return Response({
            'status': 'OK', 
            'metrics': {
                'model_loaded': hasattr(self, 'model') and self.model is not None
            }
        })

def health_check(request):
    return HttpResponse("healthy", status=200)