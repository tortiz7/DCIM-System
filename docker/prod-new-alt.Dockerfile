# Dockerfile for the web container running Ralph and Chatbot integrated from source
FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8

# Build arguments
ARG RALPH_REPO=git@github.com:tortiz7/DCIM-System.git
ARG RALPH_BRANCH=deployment-test

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
    openssh-client \
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
    netcat \
    redis-tools \
 && rm -rf /var/lib/apt/lists/* \
 && locale-gen en_US.UTF-8

# Upgrade pip and setuptools/wheel
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /app

# Set up SSH known_hosts for GitHub
RUN mkdir -p ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts && \
    chmod 600 ~/.ssh/known_hosts

# Clone the Ralph repo
# Note: Ensure that you have SSH keys set up properly for private repo access, or use a public repo/HTTPS token.
RUN --mount=type=ssh git clone --branch $RALPH_BRANCH $RALPH_REPO .

# Set environment variables for Ralph
ENV DJANGO_SETTINGS_MODULE=ralph.settings.prod
ENV PATH=/usr/local/bin:$PATH

# Set up version handling
ENV RALPH_VERSION=3.0.0
RUN chmod +x get_version.sh && \
    git config --global --add safe.directory /app

# Modify setup.py installation approach
RUN sed -i 's/subprocess.check_output(\[script\], shell=True)/os.getenv("RALPH_VERSION", "3.0.0").encode()/' setup.py && \
    pip3 install -e . && \
    which ralph && \
    ralph --version

# Alternative approach if the above doesn't work:
RUN echo '#!/bin/bash\necho "$RALPH_VERSION"' > get_version.sh && \
    chmod +x get_version.sh && \
    pip3 install -e . && \
    which ralph && \
    ralph --version

# Install Python dependencies including chatbot
RUN pip3 install --no-cache-dir \
    channels==3.0.4 \
    channels-redis==3.3.0 \
    aioredis==1.3.1 \
    websockets==10.0 \
    prometheus-client==0.11.0 \
    hiredis==2.0.0 \
    mysqlclient==2.1.1

# Install Ralph from source
# This will install the `ralph` command line tool
RUN pip3 install --no-cache-dir -r requirements/base.txt && \
    pip3 install --no-cache-dir -r requirements/openstack.txt && \
    pip3 install --no-cache-dir -r requirements/prod.txt && \
    pip3 install --no-cache-dir keystoneauth1>=3.18.0
    
RUN python3 setup.py develop && \
    which ralph && \
    ralph --version

RUN echo "Verifying Ralph installation..." && \
    if ! command -v ralph &> /dev/null; then \
        echo "Ralph command not found! Installing entry points directly..." && \
        pip3 install --no-cache-dir -e . && \
        if ! command -v ralph &> /dev/null; then \
            echo "Failed to install Ralph command" && \
            exit 1; \
        fi \
    fi

# Copy the initialization script and make it executable
COPY initialize.sh /usr/local/bin/initialize.sh
RUN chmod +x /usr/local/bin/initialize.sh

# Add healthcheck to ensure Ralph is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/usr/local/bin/initialize.sh"]
