from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.http import HttpResponse
import torch
from transformers import LlamaTokenizer, LlamaForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from transformers import AutoConfig
import logging
import os

logger = logging.getLogger(__name__)

class ChatbotView(APIView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            # Create a clean config without loading from pretrained
            from transformers import LlamaConfig
            model_config = LlamaConfig(
                vocab_size=32000,
                hidden_size=3072,
                intermediate_size=8192,
                num_attention_heads=24,
                num_hidden_layers=28,
                num_key_value_heads=8,
                rope_scaling={"type": "dynamic", "factor": 32.0},  # Clean RoPE config
                torch_dtype=torch.float16,
                use_cache=True
            )

            # Load base model with our clean config
            self.model = LlamaForCausalLM.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                config=model_config,
                device_map="auto",
                torch_dtype=torch.float16,
                quantization_config=bnb_config,
                trust_remote_code=False  # Force it to use our config
            )

            adapters_path = settings.MODEL_PATH['adapters_path']

            # Load tokenizer
            self.tokenizer = LlamaTokenizer.from_pretrained(
                "hf-internal-testing/llama-tokenizer",
                use_fast=False,
                local_files_only=False
            )

            # Apply your custom adapter
            if os.path.exists(os.path.join(adapters_path, 'adapter_config.json')):
                self.model = PeftModel.from_pretrained(
                    self.model,
                    adapters_path,  # This points to your adapter files
                    torch_dtype=torch.float16
                )
                logger.info("LoRA adapter loaded successfully")

            logger.info("Model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Error initializing ChatbotView: {e}", exc_info=True)
            self.model = None
            self.tokenizer = None

    def get(self, request):
        return Response({
            'status': 'ready',
            'model_loaded': self.model is not None and self.tokenizer is not None
        })

    def post(self, request):
        if self.model is None or self.tokenizer is None:
            return Response(
                {'error': 'Model not initialized properly'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        question = request.data.get('question')
        if not question:
            return Response({'error': 'Question is required'}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'response': response_text, 'metrics': {'status': 'success'}})
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return Response({'error': 'Error generating response'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MetricsView(APIView):
    def get(self, request):
        return Response({
            'status': 'OK',
            'metrics': {'model_loaded': self.model is not None}
        })


def health_check(request):
    return HttpResponse("healthy", status=200)
