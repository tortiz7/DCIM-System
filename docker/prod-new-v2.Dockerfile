FROM ubuntu:jammy AS ralph_fresh_build

ENV DEBIAN_FRONTEND=noninteractive

# Ralph configuration and paths
ARG RALPH_LOCAL_DIR="/var/local/ralph"
ARG RALPH_VERSION=""
ENV PATH=/opt/ralph/ralph-core/bin/:$PATH \
    RALPH_CONF_DIR="/etc/ralph" \
    RALPH_LOCAL_DIR="$RALPH_LOCAL_DIR" \
    RALPH_IMAGE_TMP_DIR="/tmp" \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONUNBUFFERED=1

# Install system dependencies - Updated for Ubuntu 22.04
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
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8
    
# Upgrade pip and install build tools
RUN python3 -m pip install --no-cache-dir pip setuptools wheel --upgrade

# Install Python dependencies for chatbot integration
RUN pip3 install --no-cache-dir \
    channels==3.0.4 \
    channels-redis==3.3.0 \
    aioredis==1.3.1 \
    websockets==10.0 \
    prometheus-client==0.11.0 \
    hiredis==2.0.0 \
    mysqlclient==2.1.1

# Copy application code
COPY . $RALPH_LOCAL_DIR/

# Set up Ralph scripts and configuration
RUN mkdir -p /var/log/ralph && \
    chmod +x /docker/provision/*.sh
  

# Install Ralph dependencies
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

RUN chmod +x docker/initialize.sh

ENTRYPOINT ["docker/initialize.sh"]