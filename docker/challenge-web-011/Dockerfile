\
# ================================================================
# Reto CTF de EclipSec
# ================================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    wget \
    ca-certificates \
    bash \
    procps \
    net-tools \
    python3 \
    python3-pip \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

# Instalar ttyd
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then TTYD_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then TTYD_ARCH="aarch64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.${TTYD_ARCH}" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# Script del reto
RUN mkdir -p /app
COPY app.py /app/app.py

# Nginx
RUN cat > /start.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
NGINXCONF

nginx -t

ttyd \
    --port 7681 \
    --writable \
    --cwd /root \
    -t title="CTF Shell" \
    --base-path /ws \
    bash &

cd /app && python3 app.py &

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chmod +x /start.sh

EXPOSE 80 7681

CMD ["/start.sh"]
