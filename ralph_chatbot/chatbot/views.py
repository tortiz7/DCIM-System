from django.views import View
from django.http import JsonResponse
from django.shortcuts import render
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import logging
from .api.client import RalphAPIClient

logger = logging.getLogger(__name__)

class ChatbotView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = RalphAPIClient()
        self.initialize_model()

    def initialize_model(self):
        try:
            # Initialize tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                trust_remote_code=True
            )
            
            # Initialize base model with proper device placement
            base_model = AutoModelForCausalLM.from_pretrained(
                "unsloth/Llama-3.2-3B-bnb-4bit",
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )

            # Load the trained LoRA adapter
            self.model = PeftModel.from_pretrained(
                base_model,
                "ralph_lora_adapters",
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            # Ensure model is in evaluation mode
            self.model.eval()
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    def generate_response(self, question, metrics=None):
        try:
            # Enhance prompt with metrics context if available
            if metrics:
                context = f"""Current System Status:
                Assets: {metrics['assets']['total_count']} total
                Network: {metrics['networks']['status']}
                Power Usage: {metrics['power']['total_consumption']}kW
                
                Question: {question}
                """
            else:
                context = question

            # Prepare input
            inputs = self.tokenizer(
                context,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.model.device)

            # Generate response
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
            
            # Get mock metrics
            metrics = self.client.fetch_metrics()
            
            # Generate AI response with metrics context
            response = self.generate_response(question, metrics)
            
            return JsonResponse({
                'response': response,
                'metrics': metrics
            })
        except Exception as e:
            logger.error(f"Error in post request: {e}")
            return JsonResponse({
                'error': str(e)
            }, status=500)


class MetricsView(APIView):
    def get(self, request):
        return Response({
            'status': 'OK',
            'metrics': {'model_loaded': self.model is not None}
        })


def health_check(request):
    return HttpResponse("healthy", status=200)
