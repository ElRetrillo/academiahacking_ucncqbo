from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MONO_DIR = BASE_DIR / "monolithic"

HTML_001 = """<!DOCTYPE html>
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
        <form method="POST" action="">
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
            <!-- Pista: ¿Has mirado debajo de la alfombra digital? EclipSec{h1dd3n_1n_pl41n_s1ght} -->
        </div>
    </div>
</body>
</html>"""

CSS_001 = (
    'body { background: radial-gradient(circle at center, #1a1a2e 0%, #16213e 100%); '
    'color: #e94560; font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; '
    'display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; '
    'overflow: hidden; } .login-card { background: rgba(22, 33, 62, 0.8); '
    'backdrop-filter: blur(10px); padding: 2.5rem; border-radius: 15px; '
    'box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); border: 1px solid rgba(233, 69, 96, 0.2); '
    'width: 100%; max-width: 400px; text-align: center; animation: fadeIn 0.8s ease-out; } '
    '@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } '
    'to { opacity: 1; transform: translateY(0); } } h1 { margin-bottom: 1.5rem; '
    'font-weight: 300; letter-spacing: 2px; text-transform: uppercase; } '
    '.input-group { margin-bottom: 1rem; text-align: left; } label { display: block; '
    'margin-bottom: 0.5rem; font-size: 0.8rem; opacity: 0.8; } input { width: 100%; '
    'padding: 0.8rem; background: #0f3460; border: 1px solid #16213e; border-radius: 5px; '
    'color: white; outline: none; transition: border 0.3s; } input:focus { border: 1px solid #e94560; } '
    'button { width: 100%; padding: 1rem; background: #e94560; color: white; border: none; '
    'border-radius: 5px; cursor: pointer; font-weight: bold; text-transform: uppercase; '
    'transition: 0.3s; margin-top: 1rem; } button:hover { background: #ff2e63; '
    'box-shadow: 0 0 15px rgba(233, 69, 96, 0.4); } .footer { margin-top: 1.5rem; '
    'font-size: 0.7rem; opacity: 0.5; }'
)


def build_monolithic_bundle(base_dir: Path, mono_dir: Path) -> None:
    """Sync standalone challenge apps into docker/monolithic and render nginx/Dockerfile."""
    mono_dir.mkdir(parents=True, exist_ok=True)

    web_001_dir = mono_dir / "web-001"
    web_001_dir.mkdir(parents=True, exist_ok=True)
    (web_001_dir / "index.html").write_text(HTML_001, encoding="utf-8")
    (web_001_dir / "style.css").write_text(CSS_001, encoding="utf-8")

    nginx_blocks = [
        """
    location /web-001/ {
        alias /app/web-001/;
        index index.html;
    }
    location /web-001/ws/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
"""
    ]
    start_cmds = [
        'ttyd --port 7681 --writable --cwd /root -t title="CTF Shell" --base-path /web-001/ws bash &'
    ]

    for i in range(2, 12):
        ch = f"{i:03d}"
        src = base_dir / f"challenge-web-{ch}" / "app.py"
        dst_dir = mono_dir / f"web-{ch}"
        dst_dir.mkdir(parents=True, exist_ok=True)

        port_web = 8000 + i
        port_ttyd = 7680 + i

        content = src.read_text(encoding="utf-8")
        content = content.replace("port=8000", f"port={port_web}")
        content = content.replace("/flag.txt", f"/flag_web{ch}.txt")
        (dst_dir / "app.py").write_text(content, encoding="utf-8")

        nginx_blocks.append(
            f"""
    location /web-{ch}/ {{
        proxy_pass http://127.0.0.1:{port_web}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
    location /web-{ch}/ws/ {{
        proxy_pass http://127.0.0.1:{port_ttyd}/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }}
"""
        )
        start_cmds.append(f"cd /app/web-{ch} && python3 app.py &")
        start_cmds.append(
            f'ttyd --port {port_ttyd} --writable --cwd /root -t title="CTF Shell" --base-path /web-{ch}/ws bash &'
        )

    start_sh = (
        """#!/bin/bash
set -e

cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        return 200 '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>EclipSec CTF Master Node</h1><p>Challenges available at /web-001/ to /web-011/</p></body></html>';
        add_header Content-Type text/html;
    }
"""
        + "".join(nginx_blocks)
        + """
}
NGINXCONF

nginx -t

"""
        + "\n".join(start_cmds)
        + """

echo "All services started."
exec nginx -g "daemon off;"
"""
    )
    (mono_dir / "start.sh").write_text(start_sh, encoding="utf-8", newline="\n")

    dockerfile = """FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \\
    nginx curl wget ca-certificates bash procps net-tools \\
    python3 python3-pip iputils-ping sqlite3 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

RUN ARCH=$(uname -m) && \\
    if [ "$ARCH" = "x86_64" ]; then TTYD_ARCH="x86_64"; \\
    elif [ "$ARCH" = "aarch64" ]; then TTYD_ARCH="aarch64"; \\
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \\
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.${TTYD_ARCH}" \\
        -o /usr/local/bin/ttyd && \\
    chmod +x /usr/local/bin/ttyd

ENV FLAG='EclipSec{sst1_t3mpl4t3_1nj3ct10n}'

COPY docker/monolithic/ /app/
RUN chmod +x /app/start.sh

RUN echo 'Welcome to the home page.' > /app/web-005/home.txt && \\
    echo 'EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}' > /flag.txt && \\
    cp /flag.txt /app/web-005/flag.txt && \\
    echo 'EclipSec{p1ng_0f_d34th_cmdi}' > /flag_web004.txt && \\
    cp /flag_web004.txt /app/web-004/flag.txt && \\
    echo 'EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}' > /flag_web011.txt && \\
    cp /flag_web011.txt /app/web-011/flag.txt

EXPOSE 80

CMD ["/app/start.sh"]
"""
    (mono_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build_monolithic_bundle(BASE_DIR, MONO_DIR)
    print("Monolithic container setup complete in docker/monolithic/")
