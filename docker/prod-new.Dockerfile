# Use Ubuntu 22.04 (Jammy) as base
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Set Ralph configuration paths
ARG RALPH_LOCAL_DIR="/var/local/ralph"
ENV PATH=/opt/ralph/ralph-core/bin/:$PATH \
    RALPH_CONF_DIR="/etc/ralph" \
    RALPH_LOCAL_DIR="$RALPH_LOCAL_DIR" \
    RALPH_IMAGE_TMP_DIR="/tmp" \
    # Set locale environment variables
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Add metadata
LABEL maintainer="Your Organization <your.email@example.com>" \
      description="Ralph DCIM with AI-powered assistant"

# Install system dependencies including Pillow requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    gnupg2 \
    locales \
    curl \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    git \
    build-essential \
    gcc \
    libldap2-dev \
    libsasl2-dev \
    libffi-dev \
    nodejs \
    npm \
    libmariadb-dev-compat \
    libmariadb-dev \
    pkg-config \
    # Pillow dependencies
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

# Set up Python environment
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install Python dependencies with specific order
WORKDIR $RALPH_LOCAL_DIR
RUN pip3 install --no-cache-dir mysqlclient && \
    pip3 install --no-cache-dir 'Django>=2.2,<3.0' && \
    pip3 install --no-cache-dir 'channels==3.0.4' && \
    pip3 install --no-cache-dir -r requirements/base.txt && \
    pip3 install --no-cache-dir 'keystoneauth1>=3.18.0' && \
    pip3 install --no-cache-dir -r requirements/openstack.txt && \
    pip3 install --no-cache-dir -r requirements/prod.txt

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Set entrypoint and default command
ENTRYPOINT ["/var/local/ralph/docker-entrypoint.sh"]
CMD ["start"]