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
            <!-- Pista: ¿Has mirado debajo de la alfombra digital? __CHALLENGE_FLAG__ -->
        </div>
    </div>
</body>
</html>
"""

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
    'font-size: 0.7rem; opacity: 0.5; }\n'
)


def build_monolithic_bundle(base_dir: Path, mono_dir: Path) -> None:
    """Sync isolated challenge apps into docker/monolithic and render nginx/Dockerfile."""
    mono_dir.mkdir(parents=True, exist_ok=True)

    web_001_dir = mono_dir / "web-001"
    web_001_dir.mkdir(parents=True, exist_ok=True)
    (web_001_dir / "index.html").write_text(HTML_001, encoding="utf-8", newline="\n")
    (web_001_dir / "style.css").write_text(CSS_001, encoding="utf-8", newline="\n")

    nginx_blocks = [
        """
    location /web-001/ {
        alias /app/web-001/;
        index index.html;
    }
"""
    ]
    start_cmds = []

    for i in range(2, 12):
        ch = f"{i:03d}"
        src = base_dir / f"challenge-web-{ch}" / "app.py"
        dst_dir = mono_dir / f"web-{ch}"
        dst_dir.mkdir(parents=True, exist_ok=True)

        port_web = 8000 + i
        content = src.read_text(encoding="utf-8").replace("port=8000", f"port={port_web}")
        (dst_dir / "app.py").write_text(content, encoding="utf-8", newline="\n")

        nginx_blocks.append(
            f"""
    location /web-{ch}/ {{
        proxy_pass http://127.0.0.1:{port_web}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
"""
        )
        if ch == "008":
            start_cmds.append(
                'su -s /bin/sh web008 -c \'cd /app/web-008 && FLAG="$(cat /app/web-008/.flag)" && export FLAG && exec python3 app.py\' &'
            )
        else:
            start_cmds.append(
                f'su -s /bin/sh web{ch} -c "cd /app/web-{ch} && exec python3 app.py" &'
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
    nginx ca-certificates bash python3 python3-pip iputils-ping sqlite3 \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir flask

RUN for uid in 002 003 004 005 006 007 008 009 010 011; do \\
        useradd --system --no-create-home --shell /usr/sbin/nologin "web${uid}"; \\
    done

ARG FLAG_WEB_001='EclipSec{h1dd3n_1n_pl41n_s1ght}'
ARG FLAG_WEB_002='EclipSec{r0b0ts_4r3_y0ur_fr13nd5}'
ARG FLAG_WEB_003='EclipSec{c00k13_m0nst3r_m4n1pul4t10n}'
ARG FLAG_WEB_004='EclipSec{p1ng_0f_d34th_cmdi}'
ARG FLAG_WEB_005='EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}'
ARG FLAG_WEB_006='EclipSec{sql1_byp4ss_l0g1n}'
ARG FLAG_WEB_007='EclipSec{1d0r_c4n_b3_d4ng3r0us}'
ARG FLAG_WEB_008='EclipSec{sst1_t3mpl4t3_1nj3ct10n}'
ARG FLAG_WEB_009='EclipSec{b4ckup_f1l3s_4r3_l34ks}'
ARG FLAG_WEB_010='EclipSec{h34d3rs_c4n_b3_sp00f3d}'
ARG FLAG_WEB_011='EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}'

COPY docker/monolithic/web-001 /app/web-001
COPY docker/monolithic/web-002 /app/web-002
COPY docker/monolithic/web-003 /app/web-003
COPY docker/monolithic/web-004 /app/web-004
COPY docker/monolithic/web-005 /app/web-005
COPY docker/monolithic/web-006 /app/web-006
COPY docker/monolithic/web-007 /app/web-007
COPY docker/monolithic/web-008 /app/web-008
COPY docker/monolithic/web-009 /app/web-009
COPY docker/monolithic/web-010 /app/web-010
COPY docker/monolithic/web-011 /app/web-011
COPY docker/monolithic/start.sh /usr/local/sbin/start.sh

RUN sed -i 's/\\r$//' /usr/local/sbin/start.sh && \\
    chown root:root /usr/local/sbin/start.sh && \\
    chmod 700 /usr/local/sbin/start.sh

RUN python3 -c "import os, pathlib; p = pathlib.Path('/app/web-001/index.html'); p.write_text(p.read_text(encoding='utf-8').replace('__CHALLENGE_FLAG__', os.environ['FLAG_WEB_001']), encoding='utf-8')" && \\
    chown -R root:www-data /app/web-001 && \\
    chmod 750 /app/web-001 && \\
    chmod 640 /app/web-001/*

RUN printf '%s\\n' "$FLAG_WEB_002" > /app/web-002/.flag && \\
    printf '%s\\n' "$FLAG_WEB_003" > /app/web-003/.flag && \\
    printf '%s\\n' "$FLAG_WEB_004" > /app/web-004/flag.txt && \\
    printf '%s\\n' 'Welcome to the home page.' > /app/web-005/home.txt && \\
    printf '%s\\n' "$FLAG_WEB_005" > /flag.txt && \\
    printf '%s\\n' "$FLAG_WEB_006" > /app/web-006/.flag && \\
    printf '%s\\n' "$FLAG_WEB_007" > /app/web-007/.flag && \\
    printf '%s\\n' "$FLAG_WEB_008" > /app/web-008/.flag && \\
    printf '%s\\n' "$FLAG_WEB_009" > /app/web-009/.flag && \\
    printf '%s\\n' "$FLAG_WEB_010" > /app/web-010/.flag && \\
    printf '%s\\n' "$FLAG_WEB_011" > /app/web-011/flag.txt && \\
    for uid in 002 003 004 005 007 008 009 010 011; do \\
        chown -R "root:web${uid}" "/app/web-${uid}" && \\
        chmod 550 "/app/web-${uid}" && \\
        chmod 440 "/app/web-${uid}/"*; \\
    done && \\
    chown root:web005 /flag.txt && chmod 440 /flag.txt && \\
    chown web006:web006 /app/web-006 && chmod 700 /app/web-006 && \\
    chown root:web006 /app/web-006/app.py /app/web-006/.flag && \\
    chmod 440 /app/web-006/app.py /app/web-006/.flag && \\
    chmod 440 /app/web-002/.flag /app/web-003/.flag /app/web-007/.flag /app/web-008/.flag /app/web-009/.flag /app/web-010/.flag

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
"""
    (mono_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build_monolithic_bundle(BASE_DIR, MONO_DIR)
    print("Monolithic container setup complete in docker/monolithic/")
