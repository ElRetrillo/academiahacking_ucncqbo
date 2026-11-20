FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/*

ARG CHALLENGE_FLAG='EclipSec{h1dd3n_1n_pl41n_s1ght}'

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

RUN cat > /var/www/html/index.html << 'HTMLDOC'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Restringido - SecureCorp</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="login-card">
        <h1>SecureCorp</h1>
        <p style="font-size: 0.9rem; margin-bottom: 2rem; opacity: 0.7;">Portal Interno de Administración</p>
        <form method="POST" action="/login">
            <div class="input-group">
                <label>Usuario</label>
                <input type="text" name="user" placeholder="Introduzca su ID" required>
            </div>
            <div class="input-group">
                <label>Contraseña</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit">Autenticar</button>
        </form>
        <div class="footer">
            &copy; 2026 SecureCorp Defence Systems. Todos los derechos reservados.
            <!-- DEBUG_MODE: Enabled -->
            <!-- Credenciales de emergencia (borrar en prod): admin / s3cur3p4ss -->
            <!-- Pista: ¿Has mirado debajo de la alfombra digital? __CHALLENGE_FLAG__ -->
        </div>
    </div>
</body>
</html>
HTMLDOC

RUN bash -c 'tpl=$(cat /var/www/html/index.html); printf "%s\n" "${tpl//__CHALLENGE_FLAG__/$CHALLENGE_FLAG}" > /var/www/html/index.html' && \
    chown -R root:www-data /var/www/html && \
    chmod 750 /var/www/html /var/www/html/assets && \
    chmod 640 /var/www/html/index.html /var/www/html/style.css

RUN cat > /usr/local/sbin/start.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

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
}
NGINXCONF

nginx -t

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chown root:root /usr/local/sbin/start.sh && chmod 700 /usr/local/sbin/start.sh

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
