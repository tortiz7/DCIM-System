FROM nginx

LABEL description="Static files and reverse proxy for Ralph DCIM"

# Copy static files from build context
COPY src/ralph/static /opt/static
COPY docker/ralph.conf.nginx /etc/nginx/conf.d/default.conf