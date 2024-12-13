# syntax=docker/dockerfile:1.4
FROM nvidia/cuda:12.4.0-devel-ubuntu22.04

# Set environment variables for Redis/Elasticache
ENV REDIS_HOST=${REDIS_HOST}
ENV REDIS_PORT=6379
ENV DB_NAME=${DATABASE_NAME}
ENV DB_USER=${DATABASE_USER}
ENV DB_PASSWORD=${DATABASE_PASSWORD}
ENV DB_HOST=${DATABASE_HOST}
ENV DB_PORT=5432
ENV ALB_DOMAIN="*"
ENV ALLOWED_HOSTS="*"

# Set environment variables for CUDA - matching G4DN setup
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}
ENV TORCH_CUDA_ARCH_LIST="7.5"
ENV FORCE_CUDA="1"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    git-lfs \
    curl \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Verify CUDA installation early
RUN nvcc --version

WORKDIR /app
ENV PYTHONPATH=/app/ralph_chatbot

RUN git lfs install

ARG CHATBOT_REPO=git@github.com:tortiz7/DCIM-System.git
ARG CHATBOT_BRANCH=chatbot-TOrtiz
RUN echo "Repo: $CHATBOT_REPO" && echo "Branch: $CHATBOT_BRANCH"

RUN mkdir -p ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts && \
    chmod 600 ~/.ssh/known_hosts
RUN --mount=type=ssh git clone --branch $CHATBOT_BRANCH $CHATBOT_REPO . && \
    git lfs pull

WORKDIR /app/ralph_chatbot

# Install Python dependencies in the correct order
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    # Install base dependencies
    pip3 install --no-cache-dir packaging ninja einops scipy && \
    # Install PyTorch with CUDA 12.1 support (closest stable version)
    pip3 install --no-cache-dir \
        torch==2.1.2 \
        torchvision==0.16.2 \
        torchaudio==2.1.2 \
        --extra-index-url https://download.pytorch.org/whl/cu121 && \
    # Install ML dependencies without verification
    pip3 install --no-cache-dir xformers==0.0.27.post2 && \
    pip3 install --no-cache-dir transformers==4.36.0 && \
    pip3 install --no-cache-dir peft==0.3.0 && \
    pip3 install --no-cache-dir bitsandbytes==0.41.1 && \
    pip3 install --no-cache-dir unsloth==2024.11.10 && \
    # Flash attention with G4DN architecture
    TORCH_CUDA_ARCH_LIST="7.5" pip3 install --no-cache-dir flash-attn==1.0.9 && \
    # Finally install remaining requirements
    pip3 install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/ralph_chatbot
ENV DJANGO_SETTINGS_MODULE=chatbot.settings
ENV NVIDIA_VISIBLE_DEVICES=all
ENV CUDA_VISIBLE_DEVICES=0
ENV MODEL_PATH=/app/ralph_chatbot/chatbot/model
ENV LORA_PATH=/app/ralph_chatbot/chatbot/model/adapters

# Initialize Django
RUN python3 manage.py collectstatic --noinput
RUN chmod +x init_chatbot.sh || true

# Add volume for static files only
VOLUME ["/app/ralph_chatbot/staticfiles"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health/ || exit 1

EXPOSE 8001 9100

# Create startup script with CUDA verification
RUN echo '#!/bin/bash\n\
echo "Verifying CUDA setup..." && \
python3 -c "import torch; print(\"CUDA available:\", torch.cuda.is_available()); print(\"CUDA version:\", torch.version.cuda); print(\"Device count:\", torch.cuda.device_count()); print(\"GPU Device:\", torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"No GPU\")" && \
echo "Starting Daphne server..." && \
exec daphne -b 0.0.0.0 -p 8001 --proxy-headers --access-log - --http-timeout 300 chatbot.asgi:application' > /start.sh && \
    chmod +x /start.sh

CMD ["/start.sh"]