# syntax=docker/dockerfile:1.4
FROM nvidia/cuda:12.4.0-devel-ubuntu22.04

# Set environment variables for Redis/Elasticache
ENV REDIS_HOST="my-redis-replication-group.9fmuyw.ng.0001.use1.cache.amazonaws.com:6379"
ENV REDIS_PORT=6379

ENV DB_NAME=ralph_ng
ENV DB_USER=cloudega2024
ENV DB_PASSWORD=cloudega2024!
ENV DB_HOST=ralphng.ct0guqq467p6.us-east-1.rds.amazonaws.com
ENV DB_PORT=5432

# Set environment variables for CUDA
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}
ENV TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6"
ENV FORCE_CUDA="1"
ENV TORCH_NVCC_FLAGS="-Xfatbin -compress-all"
# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV PYTHONPATH=/app/ralph_chatbot
ARG CHATBOT_REPO=git@github.com:tortiz7/DCIM-System.git
ARG CHATBOT_BRANCH=chatbot-TOrtiz
RUN echo "Repo: $CHATBOT_REPO" && echo "Branch: $CHATBOT_BRANCH"
RUN mkdir -p ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts && \
    chmod 600 ~/.ssh/known_hosts
RUN --mount=type=ssh git clone --branch $CHATBOT_BRANCH $CHATBOT_REPO .
WORKDIR /app/ralph_chatbot
# Install Python dependencies including Unsloth
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir packaging ninja einops && \
    # Install torch with CUDA support first
    pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir unsloth==2024.11.10 && \
    TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6" pip3 install --no-cache-dir flash-attn==1.0.9 && \
    pip3 install --no-cache-dir xformers>=0.0.27.post2 trl peft accelerate bitsandbytes
# Verify CUDA and set up environment (with error handling)
RUN python3 -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda); print('Device count:', torch.cuda.device_count())" || exit 1
ENV PYTHONPATH=/app/ralph_chatbot
ENV DJANGO_SETTINGS_MODULE=chatbot.settings
ENV NVIDIA_VISIBLE_DEVICES=all
ENV CUDA_VISIBLE_DEVICES=0
ENV MODEL_PATH=/app/ralph_chatbot/chatbot/model
ENV LORA_PATH=/app/ralph_chatbot/chatbot/model/adapters
# Add model verification on startup
RUN chmod +x chatbot/utils/verify_model.py
# Collect static files
RUN python3 manage.py collectstatic --noinput
ARG DOCKER_BUILDKIT=1
ARG SKIP_HEALTHCHECK=true
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$SKIP_HEALTHCHECK" = "true" ]; then exit 0; else curl -f http://localhost:8001/health/ || exit 1; fi
EXPOSE 8001 9100
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8001", \
     "--workers", "4", \
     "--timeout", "120", \
     "--keep-alive", "65", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "chatbot.wsgi:application"]