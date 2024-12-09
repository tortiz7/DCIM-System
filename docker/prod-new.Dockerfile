FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive

# Ralph configuration and paths
ARG RALPH_LOCAL_DIR="/var/local/ralph"
ENV PATH=/opt/ralph/ralph-core/bin/:$PATH
ENV RALPH_CONF_DIR="/etc/ralph"
ENV RALPH_LOCAL_DIR="$RALPH_LOCAL_DIR"
ENV RALPH_IMAGE_TMP_DIR="/tmp"

LABEL maintainer="Allegro.pl Sp. z o.o. opensource@allegro.pl"
LABEL authors="Allegro.pl Sp. z o.o. and Contributors opensource@allegro.pl"

# Install base dependencies
RUN apt-get clean && \
    apt-get update && \
    apt-get -y install apt-transport-https ca-certificates gnupg2 locales curl \
    python3 python3-dev python3-pip python3-setuptools \
    git libldap2-dev libsasl2-dev libffi-dev \
    nodejs npm libmysqlclient-dev=5.7.21-1ubuntu1 \
    libmysqlclient20=5.7.21-1ubuntu1 && \
    rm -rf /var/lib/apt/lists/*

# Set UTF-8 locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Copy from build context (will be /opt/ralph/source)
COPY . $RALPH_LOCAL_DIR/

# Make scripts executable and move them
RUN chmod +x $RALPH_LOCAL_DIR/docker/provision/*.sh
RUN mv $RALPH_LOCAL_DIR/docker/provision/*.sh $RALPH_LOCAL_DIR/
RUN mv $RALPH_LOCAL_DIR/docker/provision/createsuperuser.py $RALPH_LOCAL_DIR/

WORKDIR $RALPH_LOCAL_DIR
RUN pip3 install -r requirements/prod.txt

ENTRYPOINT ["/var/local/ralph/docker-entrypoint.sh"]
CMD ["start"]