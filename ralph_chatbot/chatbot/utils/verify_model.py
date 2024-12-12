# verify_model.py
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_model():
    try:
        # Get paths from environment
        model_path = os.environ.get('MODEL_PATH')
        lora_path = os.environ.get('LORA_PATH')

        if not model_path or not lora_path:
            raise ValueError("MODEL_PATH or LORA_PATH environment variables not set")

        logger.info(f"Checking paths:\nModel path: {model_path}\nLoRA path: {lora_path}")

        # Define required files and minimum sizes (in bytes)
        required_files = {
            os.path.join(model_path, 'tokenizer.json'): 1000,
            os.path.join(model_path, 'tokenizer_config.json'): 100,
            os.path.join(model_path, 'special_tokens_map.json'): 100,
            os.path.join(lora_path, 'adapter_config.json'): 100,
            os.path.join(lora_path, 'adapter_model.safetensors'): 1000000  # At least 1MB
        }

        # Check each required file
        for file_path, min_size in required_files.items():
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Required file not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size < min_size:
                raise ValueError(
                    f"File too small: {file_path}\n"
                    f"Size: {file_size/1024:.2f}KB, Expected at least: {min_size/1024:.2f}KB"
                )
            
            logger.info(f"✓ Verified {os.path.basename(file_path)} - {file_size/1024/1024:.2f}MB")

        # Check CUDA availability
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        
        logger.info(f"✓ CUDA is available - Found {torch.cuda.device_count()} device(s)")
        logger.info(f"✓ Using CUDA Device: {torch.cuda.get_device_name(0)}")

        # Test load tokenizer
        logger.info("Testing tokenizer loading...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info("✓ Tokenizer loaded successfully")

        # Test load model
        logger.info("Testing model loading...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.float16
        )
        logger.info("✓ Base model loaded successfully")

        # Test load adapter
        logger.info("Testing LoRA adapter loading...")
        model = PeftModel.from_pretrained(model, lora_path)
        logger.info("✓ LoRA adapter loaded successfully")

        # Test basic inference
        logger.info("Testing basic inference...")
        test_input = tokenizer("Hello, I am Ralph", return_tensors="pt").to(model.device)
        with torch.no_grad():
            output = model.generate(**test_input, max_length=20)
            result = tokenizer.decode(output[0], skip_special_tokens=True)
        logger.info("✓ Basic inference successful")

        logger.info("🎉 All model verification checks passed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Model verification failed: {str(e)}")
        logger.error("Detailed error:", exc_info=True)
        return False

if __name__ == "__main__":
    if not verify_model():
        exit(1)