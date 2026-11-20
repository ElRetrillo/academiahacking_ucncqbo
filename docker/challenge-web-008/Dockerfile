FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ca-certificates \
    bash \
    python3 \
    python3-pip \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir flask

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='EclipSec{sst1_t3mpl4t3_1nj3ct10n}'

RUN mkdir -p /app
COPY app.py /app/app.py

RUN printf '%s\n' "$CHALLENGE_FLAG" > /app/.flag && \
    chown -R root:ctf /app && \
    chmod 550 /app && \
    chmod 440 /app/app.py /app/.flag

RUN cat > /usr/local/sbin/start.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINXCONF

nginx -t

su -s /bin/sh ctf -c 'cd /app && FLAG="$(cat /app/.flag)" && export FLAG && exec python3 app.py' &

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chown root:root /usr/local/sbin/start.sh && chmod 700 /usr/local/sbin/start.sh

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
