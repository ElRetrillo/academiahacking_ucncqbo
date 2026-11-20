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

ARG CHALLENGE_FLAG='EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}'

RUN mkdir -p /app
COPY app.py /app/app.py

RUN printf '%s\n' 'Welcome to the home page.' > /app/home.txt && \
    printf '%s\n' "$CHALLENGE_FLAG" > /flag.txt && \
    chown -R root:ctf /app /flag.txt && \
    chmod 550 /app && \
    chmod 440 /app/app.py /app/home.txt /flag.txt

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

su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chown root:root /usr/local/sbin/start.sh && chmod 700 /usr/local/sbin/start.sh

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
