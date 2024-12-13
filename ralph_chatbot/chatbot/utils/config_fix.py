# chatbot/utils/config_fix.py
import json
import os

def fix_config():
    config_path = '/app/ralph_chatbot/chatbot/model/config.json'
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Convert rope_scaling to expected format
    if 'rope_scaling' in config:
        config['rope_scaling'] = {
            "type": "linear",
            "factor": config['rope_scaling'].get('factor', 32.0)
        }
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

if __name__ == "__main__":
    fix_config()