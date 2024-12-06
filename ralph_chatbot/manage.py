#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Handle special commands for the chatbot
    if len(sys.argv) > 1 and sys.argv[1] == 'init_chatbot':
        # Ensure model directory exists
        model_dir = Path(__file__).resolve().parent / 'chatbot' / 'model'
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure model adapters directory exists
        adapters_dir = model_dir / 'adapters'
        adapters_dir.mkdir(parents=True, exist_ok=True)

        # Create required directories for static and media files
        static_dir = Path(__file__).resolve().parent / 'static'
        static_dir.mkdir(parents=True, exist_ok=True)
        
        media_dir = Path(__file__).resolve().parent / 'media'
        media_dir.mkdir(parents=True, exist_ok=True)

        # Run migrations
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create cache tables
        execute_from_command_line(['manage.py', 'createcachetable'])
        
        print("Chatbot initialization completed successfully!")
        return

    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()