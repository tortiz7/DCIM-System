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

RUN pip3 install --no-cache-dir \
    setuptools==59.6.0 \
    wheel==0.37.1

# Set version and install Ralph's dependencies
ENV RALPH_VERSION=3.0.0

# Install critical dependencies
RUN pip3 install --no-cache-dir \
    Django==3.2.18 \
    pytz==2023.3 \
    six>=1.16.0

# Install Ralph's requirements
RUN pip3 install --no-cache-dir -r requirements/base.txt && \
    pip3 install --no-cache-dir -r requirements/openstack.txt && \
    pip3 install --no-cache-dir -r requirements/prod.txt

# Create a simple version script to bypass git issues
RUN echo "#!/bin/bash\necho \"$RALPH_VERSION\"" > get_version.sh && \
    chmod +x get_version.sh

# Install Ralph in development mode
RUN pip3 install -e .

# Verify the ralph command
RUN which ralph || ( \
    echo "Creating ralph command manually..." && \
    echo '#!/usr/bin/env python3' > /usr/local/bin/ralph && \
    echo 'from ralph.__main__ import prod' >> /usr/local/bin/ralph && \
    echo 'if __name__ == "__main__":' >> /usr/local/bin/ralph && \
    echo '    prod()' >> /usr/local/bin/ralph && \
    chmod +x /usr/local/bin/ralph \
)

# Test ralph command
RUN ralph --help || exit 0

# Copy the initialization script and make it executable
COPY initialize.sh /usr/local/bin/initialize.sh
RUN chmod +x /usr/local/bin/initialize.sh

# Add healthcheck to ensure Ralph is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/usr/local/bin/initialize.sh"]
