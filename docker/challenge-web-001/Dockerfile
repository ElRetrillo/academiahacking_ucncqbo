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


# ── Contenido web del reto (Premium UI) ───────────────────────────
RUN mkdir -p /var/www/html/assets
RUN echo 'body { \
    background: radial-gradient(circle at center, #1a1a2e 0%, #16213e 100%); \
    color: #e94560; \
    font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; \
    display: flex; \
    justify-content: center; \
    align-items: center; \
    height: 100vh; \
    margin: 0; \
    overflow: hidden; \
} \
.login-card { \
    background: rgba(22, 33, 62, 0.8); \
    backdrop-filter: blur(10px); \
    padding: 2.5rem; \
    border-radius: 15px; \
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); \
    border: 1px solid rgba(233, 69, 96, 0.2); \
    width: 100%; \
    max-width: 400px; \
    text-align: center; \
    animation: fadeIn 0.8s ease-out; \
} \
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } } \
h1 { margin-bottom: 1.5rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; } \
.input-group { margin-bottom: 1rem; text-align: left; } \
label { display: block; margin-bottom: 0.5rem; font-size: 0.8rem; opacity: 0.8; } \
input { \
    width: 100%; \
    padding: 0.8rem; \
    background: #0f3460; \
    border: 1px solid #16213e; \
    border-radius: 5px; \
    color: white; \
    outline: none; \
    transition: border 0.3s; \
} \
input:focus { border: 1px solid #e94560; } \
button { \
    width: 100%; \
    padding: 1rem; \
    background: #e94560; \
    color: white; \
    border: none; \
    border-radius: 5px; \
    cursor: pointer; \
    font-weight: bold; \
    text-transform: uppercase; \
    transition: 0.3s; \
    margin-top: 1rem; \
} \
button:hover { background: #ff2e63; box-shadow: 0 0 15px rgba(233, 69, 96, 0.4); } \
.footer { margin-top: 1.5rem; font-size: 0.7rem; opacity: 0.5; }' > /var/www/html/style.css

RUN echo '<!DOCTYPE html> \
<html lang="es"> \
<head> \
    <meta charset="UTF-8"> \
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> \
    <title>Acceso Restringido - SecureCorp</title> \
    <link rel="stylesheet" href="style.css"> \
</head> \
<body> \
    <div class="login-card"> \
        <h1>SecureCorp</h1> \
        <p style="font-size: 0.9rem; margin-bottom: 2rem; opacity: 0.7;">Portal Interno de Administración</p> \
        <form method="POST" action="/login"> \
            <div class="input-group"> \
                <label>Usuario</label> \
                <input type="text" name="user" placeholder="Introduzca su ID" required> \
            </div> \
            <div class="input-group"> \
                <label>Contraseña</label> \
                <input type="password" name="password" placeholder="••••••••" required> \
            </div> \
            <button type="submit">Autenticar</button> \
        </form> \
        <div class="footer"> \
            &copy; 2026 SecureCorp Defence Systems. Todos los derechos reservados. \
            <!-- DEBUG_MODE: Enabled --> \
            <!-- Credenciales de emergencia (borrar en prod): admin / s3cur3p4ss --> \
            <!-- Pista: ¿Has mirado debajo de la alfombra digital? EclipSec{h1dd3n_1n_pl41n_s1ght} --> \
        </div> \
    </div> \
</body> \
</html>' > /var/www/html/index.html

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
