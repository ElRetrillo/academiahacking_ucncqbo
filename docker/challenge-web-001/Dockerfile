# ================================================================
# Dockerfile de ejemplo para un reto CTF de EclipSec
# (reto tipo WEB con terminal interactiva vía ttyd)
#
# Expone:
#   - Puerto 8001 → aplicación web vulnerable (nginx)
#   - Puerto 7681 → ttyd (terminal WebSocket para xterm.js)
#
# Uso:
#   docker build -t eclipsec-web-001 .
#   docker run -d -p 8001:80 -p 7681:7681 --name web-001 eclipsec-web-001
#
# Desde la página del reto la terminal conectará a:
#   ws://localhost:7681/ws
# ================================================================

FROM ubuntu:22.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# ── Herramientas base y ttyd ─────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    wget \
    ca-certificates \
    bash \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# ── Instalar ttyd (terminal web) 1.7.4 dependiendo de arquitectura ─
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then TTYD_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then TTYD_ARCH="aarch64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.${TTYD_ARCH}" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd


# ── Contenido web del reto ────────────────────────────────────────
# Aquí va tu app vulnerable. Ejemplo simple con flag en comentario HTML:
RUN echo '<!DOCTYPE html><html><head><title>Login - SecureCorp</title></head><body><h1>SecureCorp Login Portal</h1><form method="post" action="/login"><input type="text" name="user" placeholder="Username"><input type="password" name="pass" placeholder="Password"><button type="submit">Login</button></form><!-- TODO: remove before deploy --><!-- admin credentials: admin / s3cur3p4ss --><!-- flag: EclipSec{h1dd3n_1n_pl41n_s1ght} --></body></html>' > /var/www/html/index.html

# ── Script de arranque ────────────────────────────────────────────
RUN cat > /start.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

# Create nginx config
cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    root /var/www/html;
    index index.html;
    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    # Proxy para ttyd (WebSocket)
    location /ws/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
NGINXCONF

# Verify nginx config is valid before starting
nginx -t

# Start ttyd in background
ttyd \
    --port 7681 \
    --writable \
    --cwd /root \
    -t title="CTF Shell" \
    --base-path /ws \
    bash &

# Start nginx in foreground (becomes PID 1 / main process)
exec nginx -g "daemon off;"
STARTSCRIPT
RUN chmod +x /start.sh

# ── Archivo de flag dentro del contenedor ─────────────────────────
RUN echo 'EclipSec{h1dd3n_1n_pl41n_s1ght}' > /flag.txt && chmod 644 /flag.txt

# ── Exponer puertos ───────────────────────────────────────────────
EXPOSE 80 7681

CMD ["/start.sh"]
