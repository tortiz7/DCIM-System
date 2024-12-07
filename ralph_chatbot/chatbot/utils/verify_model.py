# verify_model.py
import os
from unsloth import FastLanguageModel
import torch

def verify_model():
    try:
        # Check model files exist
        model_path = os.environ['MODEL_PATH']
        lora_path = os.environ['LORA_PATH']
        required_files = [
            os.path.join(model_path, 'tokenizer.json'),
            os.path.join(model_path, 'tokenizer_config.json'),
            os.path.join(model_path, 'special_tokens_map.json'),
            os.path.join(lora_path, 'adapter_config.json'),
            os.path.join(lora_path, 'adapter_model.safetensors')
        ]
        
        for file in required_files:
            assert os.path.exists(file), f"Missing required file: {file}"
            
        # Test model loading with Unsloth
        model_name = "unsloth/Llama-3.2-8b-bnb-4bit"
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=2048,
            load_in_4bit=True
        )
        
        # Test GPU availability
        assert torch.cuda.is_available()
        assert torch.cuda.device_count() > 0
        
        print("Model verification successful!")
        return True
        
    except Exception as e:
        print(f"Model verification failed: {e}")
        return False

if __name__ == "__main__":
    if not verify_model():
        exit(1)