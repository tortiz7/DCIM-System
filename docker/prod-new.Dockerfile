FROM ubuntu:bionic

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
    LC_ALL=en_US.UTF-8

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

# Install Python dependencies for chatbot integration
RUN pip3 install --no-cache-dir \
    channels==3.0.4 \
    channels-redis==3.3.0 \
    aioredis==1.3.1 \
    websockets==10.0 \
    prometheus-client==0.11.0 \
    hiredis==2.0.0

# Copy application code
COPY . $RALPH_LOCAL_DIR/

# Set up Ralph scripts and configuration
RUN chmod +x $RALPH_LOCAL_DIR/docker/provision/*.sh \
    && mv $RALPH_LOCAL_DIR/docker/provision/*.sh $RALPH_LOCAL_DIR/ \
    && mv $RALPH_LOCAL_DIR/docker/provision/createsuperuser.py $RALPH_LOCAL_DIR/ \
    && mkdir -p /var/log/ralph

WORKDIR $RALPH_LOCAL_DIR
RUN pip3 install --no-cache-dir -r requirements/prod.txt

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/var/local/ralph/docker-entrypoint.sh"]
CMD ["start"]