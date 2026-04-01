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

# ── Herramientas base ────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    wget \
    ca-certificates \
    bash \
    procps \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# ── Instalar ttyd (terminal web) ─────────────────────────────────
# Descarga el binario precompilado de la release oficial
RUN TTYD_VERSION=$(curl -s https://api.github.com/repos/tsl0922/ttyd/releases/latest \
        | grep tag_name | cut -d'"' -f4) && \
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# ── Contenido web del reto ────────────────────────────────────────
# Aquí va tu app vulnerable. Ejemplo simple con flag en comentario HTML:
RUN echo '<!DOCTYPE html><html><head><title>Login - SecureCorp</title></head><body><h1>SecureCorp Login Portal</h1><form method="post" action="/login"><input type="text" name="user" placeholder="Username"><input type="password" name="pass" placeholder="Password"><button type="submit">Login</button></form><!-- TODO: remove before deploy --><!-- admin credentials: admin / s3cur3p4ss --><!-- flag: EclipSec{h1dd3n_1n_pl41n_s1ght} --></body></html>' > /var/www/html/index.html

# ── Script de arranque ────────────────────────────────────────────
RUN printf '#!/bin/bash\n\
set -e\n\
# Iniciar nginx en background\n\
nginx -g "daemon off;" &\n\
# Iniciar ttyd en foreground\n\
exec ttyd \\\n\
    --port 7681 \\\n\
    --writable \\\n\
    --once=false \\\n\
    --cwd /root \\\n\
    --title "CTF Shell" \\\n\
    bash\n' > /start.sh && chmod +x /start.sh

# ── Archivo de flag dentro del contenedor ─────────────────────────
RUN echo 'EclipSec{h1dd3n_1n_pl41n_s1ght}' > /flag.txt && chmod 644 /flag.txt

# ── Exponer puertos ───────────────────────────────────────────────
EXPOSE 80 7681

CMD ["/start.sh"]
