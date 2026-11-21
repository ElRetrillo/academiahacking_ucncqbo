import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MONO_DIR = BASE_DIR / "monolithic"

CHALLENGE_TILES = [
    ("001", "Hidden in Plain Sight"),
    ("002", "Robots & Crawlers"),
    ("003", "Cookie Tampering"),
    ("004", "Ping of Death"),
    ("005", "LFI to RCE"),
    ("006", "SQLi Login Bypass"),
    ("007", "IDOR Profiles"),
    ("008", "Server-Side Template Injection"),
    ("009", "Source Code Leak"),
    ("010", "Headers Matter"),
    ("011", "Command Execution GET"),
]


def render_master_index() -> str:
    tiles_html = "\n".join(
        f'                    <a class="ctf-tile" href="/web-{cid}/">'
        f'<span class="ctf-badge">web-{cid}</span>'
        f"<span>{title}</span></a>"
        for cid, title in CHALLENGE_TILES
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        "<head>\n"
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '    <meta name="robots" content="noindex, nofollow">\n'
        "    <title>Nodo de Retos | EclipSec CTF</title>\n"
        '    <link rel="stylesheet" href="global.css">\n'
        "</head>\n"
        "<body>\n"
        '    <div class="ctf-shell">\n'
        '        <main id="main-content" class="ctf-card ctf-card--wide">\n'
        '            <header class="ctf-header">\n'
        '                <span class="ctf-badge">EclipSec CTF</span>\n'
        "                <h1>EclipSec CTF Master Node</h1>\n"
        '                <p class="ctf-lead">Retos web disponibles en /web-001/ hasta /web-011/.</p>\n'
        "            </header>\n"
        '            <section class="ctf-section">\n'
        '                <nav aria-label="Retos disponibles" class="ctf-grid">\n'
        f"{tiles_html}\n"
        "                </nav>\n"
        "            </section>\n"
        '            <footer class="ctf-footer">\n'
        "                &copy; 2026 EclipSec Academia de Hacking Competitivo UCN Coquimbo.\n"
        "            </footer>\n"
        "        </main>\n"
        "    </div>\n"
        "</body>\n"
        "</html>\n"
    )


def _prune_legacy_monolithic_copies(mono_dir: Path) -> None:
    for i in range(1, 12):
        legacy_dir = mono_dir / f"web-{i:03d}"
        if legacy_dir.exists():
            shutil.rmtree(legacy_dir)
    legacy_index_css = mono_dir / "web-index" / "global.css"
    if legacy_index_css.exists():
        legacy_index_css.unlink()


def build_monolithic_bundle(base_dir: Path, mono_dir: Path) -> None:
    """Render monolithic Dockerfile/start.sh/index without duplicating challenge source files."""
    mono_dir.mkdir(parents=True, exist_ok=True)
    _prune_legacy_monolithic_copies(mono_dir)

    web_index_dir = mono_dir / "web-index"
    web_index_dir.mkdir(parents=True, exist_ok=True)
    (web_index_dir / "index.html").write_text(
        render_master_index(), encoding="utf-8", newline="\n"
    )

    nginx_blocks = [
        """
    location /web-001/ {
        alias /app/web-001/;
        index index.html;
    }
"""
    ]
    copy_blocks = [
        "COPY docker/monolithic/web-index/index.html /app/web-index/index.html",
        "COPY docker/shared/global.css /app/web-index/global.css",
        "COPY docker/challenge-web-001/index.html /app/web-001/index.html",
        "COPY docker/shared/global.css /app/web-001/global.css",
    ]
    start_cmds = []

    for i in range(2, 12):
        ch = f"{i:03d}"
        port_web = 8000 + i
        copy_blocks.append(
            f"COPY docker/challenge-web-{ch}/app.py docker/shared/ui.py docker/shared/global.css /app/web-{ch}/"
        )
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
        start_cmds.append(
            f'setpriv --reuid=web{ch} --regid=web{ch} --clear-groups sh -c "cd /app/web-{ch} && HOST=127.0.0.1 PORT={port_web} exec python3 app.py" &'
        )

    start_sh = (
        """#!/bin/bash
set -e

LISTEN_PORT="${PORT:-80}"

cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen __PORT__ default_server;
    listen [::]:__PORT__ default_server;
    server_name _;

    add_header X-Robots-Tag "noindex, nofollow" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;

    location = /global.css {
        alias /app/web-index/global.css;
    }

    location / {
        root /app/web-index;
        index index.html;
        try_files $uri $uri/ =404;
    }
"""
        + "".join(nginx_blocks)
        + """
}
NGINXCONF

sed -i "s/__PORT__/${LISTEN_PORT}/g" /etc/nginx/sites-available/default

nginx -t

"""
        + "\n".join(start_cmds)
        + """

echo "All services started."
exec nginx -g "daemon off;"
"""
    )
    (mono_dir / "start.sh").write_text(start_sh, encoding="utf-8", newline="\n")

    copies_rendered = "\n".join(copy_blocks)
    dockerfile = f"""FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \\
    PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \\
    nginx ca-certificates iputils-ping sqlite3 util-linux \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN for uid in 002 003 004 005 006 007 008 009 010 011; do \\
        useradd --system --no-create-home --shell /usr/sbin/nologin "web${{uid}}"; \\
    done

ARG FLAG_WEB_001='EclipSec{{h1dd3n_1n_pl41n_s1ght}}'
ARG FLAG_WEB_002='EclipSec{{r0b0ts_4r3_y0ur_fr13nd5}}'
ARG FLAG_WEB_003='EclipSec{{c00k13_m0nst3r_m4n1pul4t10n}}'
ARG FLAG_WEB_004='EclipSec{{p1ng_0f_d34th_cmdi}}'
ARG FLAG_WEB_005='EclipSec{{l0c4l_f1l3_1nclus10n_m4st3r}}'
ARG FLAG_WEB_006='EclipSec{{sql1_byp4ss_l0g1n}}'
ARG FLAG_WEB_007='EclipSec{{1d0r_c4n_b3_d4ng3r0us}}'
ARG FLAG_WEB_008='EclipSec{{sst1_t3mpl4t3_1nj3ct10n}}'
ARG FLAG_WEB_009='EclipSec{{b4ckup_f1l3s_4r3_l34ks}}'
ARG FLAG_WEB_010='EclipSec{{h34d3rs_c4n_b3_sp00f3d}}'
ARG FLAG_WEB_011='EclipSec{{c0mm4nd_3x3cut10n_v1a_g3t}}'

{copies_rendered}
COPY docker/monolithic/start.sh /usr/local/sbin/start.sh

RUN sed -i 's/\\r$//' /usr/local/sbin/start.sh && \\
    chown root:root /usr/local/sbin/start.sh && \\
    chmod 700 /usr/local/sbin/start.sh

RUN python3 -c "import os, pathlib; p = pathlib.Path('/app/web-001/index.html'); p.write_text(p.read_text(encoding='utf-8').replace('__CHALLENGE_FLAG__', os.environ['FLAG_WEB_001']), encoding='utf-8')" && \\
    chown -R root:www-data /app/web-001 /app/web-index && \\
    chmod 550 /app/web-001 /app/web-index && \\
    chmod 440 /app/web-001/* /app/web-index/*

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
        chown -R "root:web${{uid}}" "/app/web-${{uid}}" && \\
        chmod 550 "/app/web-${{uid}}" && \\
        chmod 440 "/app/web-${{uid}}/"*; \\
    done && \\
    chown root:web005 /flag.txt && chmod 440 /flag.txt && \\
    chown web006:web006 /app/web-006 && chmod 700 /app/web-006 && \\
    chown root:web006 /app/web-006/app.py /app/web-006/ui.py /app/web-006/global.css /app/web-006/.flag && \\
    chmod 440 /app/web-006/app.py /app/web-006/ui.py /app/web-006/global.css /app/web-006/.flag

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
"""
    (mono_dir / "Dockerfile").write_text(dockerfile, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    build_monolithic_bundle(BASE_DIR, MONO_DIR)
    print("Monolithic container setup complete in docker/monolithic/")
