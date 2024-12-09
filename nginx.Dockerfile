FROM nginx

ARG RALPH_VERSION=""

LABEL description="Static files and reverse proxy for Ralph DCIM"

# Copy your modified static files
COPY src/ralph/static /opt/static

# Copy nginx configuration
COPY contrib/docker/ralph.conf.nginx /etc/nginx/conf.d/default.conf
