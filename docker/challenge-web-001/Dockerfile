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
    ttyd \
    && rm -rf /var/lib/apt/lists/*


# ── Contenido web del reto ────────────────────────────────────────
# Aquí va tu app vulnerable. Ejemplo simple con flag en comentario HTML:
RUN echo '<!DOCTYPE html><html><head><title>Login - SecureCorp</title></head><body><h1>SecureCorp Login Portal</h1><form method="post" action="/login"><input type="text" name="user" placeholder="Username"><input type="password" name="pass" placeholder="Password"><button type="submit">Login</button></form><!-- TODO: remove before deploy --><!-- admin credentials: admin / s3cur3p4ss --><!-- flag: EclipSec{h1dd3n_1n_pl41n_s1ght} --></body></html>' > /var/www/html/index.html

# ── Script de arranque ────────────────────────────────────────────
RUN printf '#!/bin/bash\n\
set -e\n\
# Configurar nginx para usar $PORT (Railway) o 80 por defecto\n\
PORT="${PORT:-80}"\n\
cat <<EOF > /etc/nginx/sites-available/default\n\
server {\n\
    listen ${PORT} default_server;\n\
    listen [::]:${PORT} default_server;\n\
    root /var/www/html;\n\
    index index.html;\n\
    server_name _;\n\
\n\
    location / {\n\
        try_files \\$uri \\$uri/ =404;\n\
    }\n\
\n\
    # Proxy para ttyd (WebSocket)\n\
    location /ws/ {\n\
        proxy_pass http://127.0.0.1:7681/;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade \\$http_upgrade;\n\
        proxy_set_header Connection "upgrade";\n\
        proxy_set_header Host \\$host;\n\
    }\n\
}\n\
EOF\n\
\n\
# Iniciar nginx en background\n\
nginx -g "daemon off;" &\n\
\n\
# Iniciar ttyd en foreground\n\
exec ttyd \\\n\
    --port 7681 \\\n\
    --writable \\\n\
    --once=false \\\n\
    --cwd /root \\\n\
    --title "CTF Shell" \\\n\
    --base-path /ws \\\n\
    bash\n' > /start.sh && chmod +x /start.sh

# ── Archivo de flag dentro del contenedor ─────────────────────────
RUN echo 'EclipSec{h1dd3n_1n_pl41n_s1ght}' > /flag.txt && chmod 644 /flag.txt

# ── Exponer puertos ───────────────────────────────────────────────
EXPOSE 80 7681

CMD ["/start.sh"]
