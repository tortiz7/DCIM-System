FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive

# Ralph configuration and paths
ARG RALPH_LOCAL_DIR="/var/local/ralph"
ARG RALPH_VERSION=""
ENV PATH=/opt/ralph/ralph-core/bin/:$PATH
ENV RALPH_CONF_DIR="/etc/ralph"
ENV RALPH_LOCAL_DIR="$RALPH_LOCAL_DIR"
ENV RALPH_IMAGE_TMP_DIR="/tmp"

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Advanced Asset Management and DCIM system with ChatBot integration"

# Install base dependencies
RUN apt-get clean && \
    apt-get update && \
    apt-get -y install apt-transport-https ca-certificates gnupg2 locales curl && \
    rm -rf /var/lib/apt/lists/*

# Set UTF-8 locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install Ralph dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 python3-dev python3-pip python3-setuptools \
    git libldap2-dev libsasl2-dev libffi-dev \
    nodejs npm libmysqlclient-dev=5.7.21-1ubuntu1 \
    libmysqlclient20=5.7.21-1ubuntu1

# Copy your modified Ralph source code
COPY . $RALPH_LOCAL_DIR/

# Copy provision scripts
COPY docker/provision/docker-entrypoint.sh \
     docker/provision/createsuperuser.py \
     docker/provision/start-ralph.sh \
     docker/provision/wait-for-it.sh \
     docker/provision/init-ralph.sh \
     docker/provision/install_ralph.sh $RALPH_IMAGE_TMP_DIR/

RUN chmod +x $RALPH_IMAGE_TMP_DIR/*.sh && \
    mv $RALPH_IMAGE_TMP_DIR/*.sh $RALPH_LOCAL_DIR/ && \
    mv $RALPH_IMAGE_TMP_DIR/createsuperuser.py $RALPH_LOCAL_DIR/

WORKDIR $RALPH_LOCAL_DIR
RUN pip3 install -r requirements/prod.txt

ENTRYPOINT ["/var/local/ralph/docker-entrypoint.sh"]
CMD ["start"]