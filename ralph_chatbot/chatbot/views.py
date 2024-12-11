from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import HttpResponse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging

logger = logging.getLogger(__name__)

class ChatbotView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Load base model
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.MODEL_PATH['base_path'],
                device_map="auto"
            )
            # Load adapter model
            self.model = PeftModel.from_pretrained(
                self.model, 
                settings.MODEL_PATH['adapters_path']
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.MODEL_PATH['base_path']
            )
        except Exception as e:
            logger.error(f"Error initializing ChatbotView: {str(e)}")
            raise

    def post(self, request):
        question = request.data.get('question')
        if not question:
            return Response(
                {'error': 'Question is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Just a placeholder metrics dictionary since we are standalone
            metrics = {"info": "No external metrics available in standalone mode"}

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
                'metrics': metrics
            })
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MetricsView(APIView):
    def get(self, request):
        # Standalone placeholder response
        return Response({'status': 'OK', 'message': 'Standalone metrics placeholder'}, status=200)

def health_check(request):
    return HttpResponse("healthy", status=200)
