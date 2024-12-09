# Use Ubuntu 18.04 (Bionic) as base
FROM ubuntu:bionic

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
      description="Ralph DCIM with AI-powered assistant" \
      runtime.nvidia.com/visible-devices=all \
      runtime.nvidia.com/cuda.driver.major="12" \
      runtime.nvidia.com/cuda.driver.minor="4"

# Install system dependencies
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
    libldap2-dev \
    libsasl2-dev \
    libffi-dev \
    nodejs \
    npm \
    libmysqlclient-dev=5.7.21-1ubuntu1 \
    libmysqlclient20=5.7.21-1ubuntu1 \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

# Set up Python environment
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy application code
COPY . $RALPH_LOCAL_DIR/

# Set up Ralph scripts and configuration
RUN chmod +x $RALPH_LOCAL_DIR/docker/provision/*.sh \
    && mv $RALPH_LOCAL_DIR/docker/provision/*.sh $RALPH_LOCAL_DIR/ \
    && mv $RALPH_LOCAL_DIR/docker/provision/createsuperuser.py $RALPH_LOCAL_DIR/ \
    && mkdir -p /var/log/ralph

# Install Python dependencies
WORKDIR $RALPH_LOCAL_DIR
RUN pip3 install --no-cache-dir -r requirements/prod.txt

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Set entrypoint and default command
ENTRYPOINT ["/var/local/ralph/docker-entrypoint.sh"]
CMD ["start"]