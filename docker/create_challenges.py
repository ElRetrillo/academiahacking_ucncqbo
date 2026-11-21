from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SHARED_DIR = BASE_DIR / "shared"
GLOBAL_CSS_SRC = SHARED_DIR / "global.css"
UI_PY_SRC = SHARED_DIR / "ui.py"

HTML_001 = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Acceso Restringido | SecureCorp</title>
    <link rel="stylesheet" href="global.css">
</head>
<body>
    <div class="ctf-shell">
        <main id="main-content" class="ctf-card">
            <header class="ctf-header">
                <span class="ctf-badge">Acceso Interno</span>
                <h1>SecureCorp</h1>
                <p class="ctf-lead">Portal Interno de Administracion</p>
            </header>
            <section class="ctf-section">
                <form method="POST" action="/login" class="ctf-form">
                    <div class="ctf-field">
                        <label class="ctf-label" for="user-id">Usuario</label>
                        <input class="ctf-input" id="user-id" type="text" name="user" placeholder="Introduzca su ID" required>
                    </div>
                    <div class="ctf-field">
                        <label class="ctf-label" for="user-pass">Contrasena</label>
                        <input class="ctf-input" id="user-pass" type="password" name="password" placeholder="Contrasena" required>
                    </div>
                    <button type="submit" class="ctf-btn ctf-btn--primary">Autenticar</button>
                </form>
            </section>
            <footer class="ctf-footer">
                &copy; 2026 SecureCorp Defence Systems. Todos los derechos reservados.
                <!-- DEBUG_MODE: Enabled -->
                <!-- Credenciales de emergencia (borrar en prod): admin / s3cur3p4ss -->
                <!-- Pista: Has mirado debajo de la alfombra digital? __CHALLENGE_FLAG__ -->
            </footer>
        </main>
    </div>
</body>
</html>
"""

NGINX_CONF_001 = """worker_processes auto;
pid /tmp/nginx.pid;

events {
    worker_connections 256;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    client_body_temp_path /tmp/client_temp;
    proxy_temp_path /tmp/proxy_temp;
    fastcgi_temp_path /tmp/fastcgi_temp;
    uwsgi_temp_path /tmp/uwsgi_temp;
    scgi_temp_path /tmp/scgi_temp;
    access_log off;
    error_log /dev/stderr warn;

    server {
        listen 8080 default_server;
        listen [::]:8080 default_server;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        add_header X-Robots-Tag "noindex, nofollow" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer" always;

        location / {
            try_files $uri $uri/ =404;
        }
    }
}
"""

DOCKERFILE_001 = """FROM nginx:1.27-alpine

ARG CHALLENGE_FLAG='EclipSec{h1dd3n_1n_pl41n_s1ght}'

ENV PORT=8080

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
COPY global.css /usr/share/nginx/html/global.css

RUN awk 'BEGIN { flag = ENVIRON["CHALLENGE_FLAG"] } { idx = index($0, "__CHALLENGE_FLAG__"); if (idx > 0) { $0 = substr($0, 1, idx - 1) flag substr($0, idx + 18) } print }' /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp && \\
    mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html && \\
    chown -R root:nginx /usr/share/nginx/html && \\
    chmod 550 /usr/share/nginx/html && \\
    chmod 440 /usr/share/nginx/html/index.html /usr/share/nginx/html/global.css

USER nginx

EXPOSE 8080

ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
"""

CHALLENGES = [
    {
        "id": "002",
        "name": "Robots & Crawlers",
        "type": "EASY - WEB",
        "port_web": 8002,
        "default_flag": "EclipSec{r0b0ts_4r3_y0ur_fr13nd5}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import os
from pathlib import Path

from flask import Flask, Response
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    body = '<p class="ctf-muted">Bienvenido al portal publico de SecureCorp. Sin novedades operativas.</p>'
    return render_page(
        title="SecureCorp",
        heading="SecureCorp",
        subtitle="Sitio corporativo publico",
        badge="Web Corporativa",
        body_html=body,
    )


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\\nDisallow: /secret_flag_dir_991\\n", mimetype="text/plain; charset=utf-8")


@app.route("/secret_flag_dir_991")
def flag():
    return Response(read_flag(), mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "003",
        "name": "Cookie Tampering",
        "type": "EASY - WEB",
        "port_web": 8003,
        "default_flag": "EclipSec{c00k13_m0nst3r_m4n1pul4t10n}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import html
import os
from pathlib import Path

from flask import Flask, make_response, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    role = request.cookies.get("role", "guest")
    if role == "admin":
        body = f'<p class="ctf-alert ctf-alert--success">Acceso administrativo verificado: {html.escape(read_flag())}</p>'
        return render_page(
            title="Panel Admin",
            heading="Bienvenido Administrador",
            subtitle="Sesion privilegiada activa",
            badge="Control de Rol",
            body_html=body,
        )

    body = '<p class="ctf-alert ctf-alert--info">Sesion actual: invitado. Se requiere rol de administrador.</p>'
    resp = make_response(
        render_page(
            title="Panel Invitado",
            heading="Bienvenido Invitado",
            subtitle="No cuentas con privilegios de administrador",
            badge="Control de Rol",
            body_html=body,
        )
    )
    resp.set_cookie("role", "guest")
    return resp


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "004",
        "name": "Ping of Death",
        "type": "MEDIUM - WEB",
        "port_web": 8004,
        "default_flag": "EclipSec{p1ng_0f_d34th_cmdi}",
        "extra_apt": (
            "RUN apt-get update && apt-get install -y --no-install-recommends \\\n"
            "    iputils-ping \\\n"
            "    && rm -rf /var/lib/apt/lists/*\n\n"
        ),
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/flag.txt && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/flag.txt"
        ),
        "script": """
import os
import subprocess

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

BODY_TEMPLATE = (
    '<form method="POST" action="" class="ctf-form">'
    '<div class="ctf-field">'
    '<label class="ctf-label" for="ping-ip">Direccion IP o host</label>'
    '<input class="ctf-input" id="ping-ip" type="text" name="ip" value="127.0.0.1" required>'
    "</div>"
    '<button type="submit" class="ctf-btn ctf-btn--primary">Ejecutar Ping</button>'
    "</form>"
    '<pre class="ctf-output">{{ output }}</pre>'
)
PAGE_TEMPLATE = render_page(
    title="Diagnostico de Red",
    heading="Herramienta de Diagnostico",
    subtitle="Comprueba la conectividad ICMP hacia un nodo destino.",
    badge="Diagnostico",
    body_html=BODY_TEMPLATE,
    wide=True,
)


@app.route("/", methods=["GET", "POST"])
def index():
    output = ""
    if request.method == "POST":
        ip = request.form.get("ip", "")
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                f"ping -c 1 {ip}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            output = result.stdout
        except subprocess.TimeoutExpired:
            output = "Command timed out"
    return render_template_string(PAGE_TEMPLATE, output=output)


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "005",
        "name": "LFI to RCE",
        "type": "MEDIUM - WEB",
        "port_web": 8005,
        "default_flag": "EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' 'Welcome to the home page.' > /app/home.txt && \\\n"
            "    printf '%s\\n' \"$CHALLENGE_FLAG\" > /flag.txt && \\\n"
            "    chown -R root:ctf /app /flag.txt && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/home.txt /flag.txt"
        ),
        "script": """
import html
import os

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)


@app.route("/")
def index():
    file_path = request.args.get("file", "home.txt")
    try:
        # Intentional local file inclusion vulnerability for CTF training
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            content = html.escape(fh.read())
    except Exception:
        content = "File not found"

    body = (
        '<nav aria-label="Archivos" class="ctf-nav">'
        '<a class="ctf-link" href="?file=home.txt">Inicio (home.txt)</a>'
        "</nav>"
        f'<pre class="ctf-output">{content}</pre>'
    )
    return render_page(
        title="Visor de Archivos",
        heading="Visor Corporativo",
        subtitle="Lectura de documentos del servidor.",
        badge="Archivo Local",
        body_html=body,
        wide=True,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "006",
        "name": "SQLi Login Bypass",
        "type": "MEDIUM - WEB",
        "port_web": 8006,
        "default_flag": "EclipSec{sql1_byp4ss_l0g1n}",
        "extra_apt": "",
        "extra_env": "ENV CTF_DB_PATH=/tmp/users.db\n\n",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import html
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

BASE_DIR = Path(__file__).resolve().parent
FLAG_PATH = BASE_DIR / ".flag"


def get_db_path() -> Path:
    return Path(os.environ.get("CTF_DB_PATH", str(BASE_DIR / "users.db")))


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


def init_db() -> Path:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")
        count = c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
        if count == 0:
            c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
        conn.commit()
    return db_path


BODY_TEMPLATE = (
    '<form method="POST" action="" class="ctf-form">'
    '<div class="ctf-field">'
    '<label class="ctf-label" for="login-user">Usuario</label>'
    '<input class="ctf-input" id="login-user" type="text" name="user" placeholder="Username">'
    "</div>"
    '<div class="ctf-field">'
    '<label class="ctf-label" for="login-pass">Contrasena</label>'
    '<input class="ctf-input" id="login-pass" type="password" name="pass" placeholder="Password">'
    "</div>"
    '<button type="submit" class="ctf-btn ctf-btn--primary">Iniciar Sesion</button>'
    "</form>"
    "{% if error %}"
    '<p class="ctf-alert ctf-alert--error">{{ error }}</p>'
    "{% endif %}"
)
PAGE_TEMPLATE = render_page(
    title="Admin Login",
    heading="Acceso Administrativo",
    subtitle="Autenticacion interna de operadores.",
    badge="SQLite Auth",
    body_html=BODY_TEMPLATE,
)


@app.route("/", methods=["GET", "POST"])
def index():
    db_path = init_db()
    error = ""
    if request.method == "POST":
        u = request.form.get("user", "")
        p = request.form.get("pass", "")
        with closing(sqlite3.connect(db_path)) as conn:
            c = conn.cursor()
            # Intentional SQL injection vulnerability for CTF training
            query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
            try:
                c.execute(query)
                if c.fetchone():
                    success_body = f'<p class="ctf-alert ctf-alert--success">Acceso concedido: {html.escape(read_flag())}</p>'
                    return render_page(
                        title="Bienvenido Admin",
                        heading="Bienvenido Administrador",
                        subtitle="Sesion iniciada correctamente.",
                        badge="SQLite Auth",
                        body_html=success_body,
                    )
                error = "Invalid credentials"
            except Exception as exc:
                error = str(exc)
    return render_template_string(PAGE_TEMPLATE, error=error)


if __name__ == "__main__":
    init_db()
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "007",
        "name": "IDOR Profiles",
        "type": "MEDIUM - WEB",
        "port_web": 8007,
        "default_flag": "EclipSec{1d0r_c4n_b3_d4ng3r0us}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import html
import os
from pathlib import Path

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    profiles = {
        "1": "Alice - Normal User",
        "2": "Bob - Normal User",
        "0": f"Admin - {read_flag()}",
    }
    uid = request.args.get("id", "1")
    profile = profiles.get(uid, "User not found")
    alert_class = "ctf-alert ctf-alert--success" if uid == "0" else "ctf-alert ctf-alert--info"
    body = (
        f'<p class="{alert_class}">{html.escape(profile)}</p>'
        '<nav aria-label="Perfiles" class="ctf-nav">'
        '<a class="ctf-link" href="?id=1">Ver Alice</a>'
        '<a class="ctf-link" href="?id=2">Ver Bob</a>'
        "</nav>"
    )
    return render_page(
        title="Perfiles de Usuario",
        heading="Directorio de Perfiles",
        subtitle="Consulta de fichas de usuario registradas.",
        badge="Directorio",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "008",
        "name": "Server-Side Template Injection",
        "type": "HARD - WEB",
        "port_web": 8008,
        "default_flag": "EclipSec{sst1_t3mpl4t3_1nj3ct10n}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import os
from pathlib import Path

from flask import Flask, render_template_string, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def ensure_flag_env() -> None:
    if FLAG_PATH.exists() and "FLAG" not in os.environ:
        os.environ["FLAG"] = FLAG_PATH.read_text(encoding="utf-8").strip()


ensure_flag_env()


@app.route("/")
def index():
    ensure_flag_env()
    name = request.args.get("name", "Guest")
    # Intentional SSTI vulnerability for CTF training
    body = (
        f'<p class="ctf-lead">Bienvenido, {name}.</p>'
        '<p class="ctf-muted">Intenta localizar la flag en variables de entorno o archivos.</p>'
    )
    template = render_page(
        title="Motor de Plantillas",
        heading="Portal de Bienvenida",
        subtitle="Renderizado dinamico de saludo personalizado.",
        badge="Template Engine",
        body_html=body,
    )
    return render_template_string(template)


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "009",
        "name": "Source Code Leak",
        "type": "EASY - WEB",
        "port_web": 8009,
        "default_flag": "EclipSec{b4ckup_f1l3s_4r3_l34ks}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import os
from pathlib import Path

from flask import Flask, Response
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    body = '<p class="ctf-muted">Sistema endurecido sin copias de respaldo expuestas en produccion.</p>'
    return render_page(
        title="Sistema Seguro",
        heading="Sistema de Autenticacion",
        subtitle="Despliegue limpio en produccion.",
        badge="Source Audit",
        body_html=body,
    )


@app.route("/index.bak")
def bak():
    content = (
        "# Backup file\\n"
        "def login():\\n"
        f'    password = "{read_flag()}"\\n'
    )
    return Response(content, mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "010",
        "name": "Headers Matter",
        "type": "MEDIUM - WEB",
        "port_web": 8010,
        "default_flag": "EclipSec{h34d3rs_c4n_b3_sp00f3d}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag"
        ),
        "script": """
import html
import os
from pathlib import Path

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)

FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route("/")
def index():
    ua = request.headers.get("User-Agent", "")
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.remote_addr or "")

    if "SecureBrowser1.0" not in ua:
        body = '<p class="ctf-alert ctf-alert--error">Acceso denegado: solo se permite SecureBrowser1.0.</p>'
        return render_page(
            title="Acceso Denegado",
            heading="Control de Acceso",
            subtitle="Validacion estricta de cabeceras HTTP.",
            badge="Gateway",
            body_html=body,
        )

    if client_ip != "127.0.0.1":
        body = '<p class="ctf-alert ctf-alert--error">Acceso denegado: solo conexiones locales (127.0.0.1).</p>'
        return render_page(
            title="Acceso Denegado",
            heading="Control de Acceso",
            subtitle="Validacion estricta de cabeceras HTTP.",
            badge="Gateway",
            body_html=body,
        )

    body = f'<p class="ctf-alert ctf-alert--success">Acceso concedido: {html.escape(read_flag())}</p>'
    return render_page(
        title="Acceso Concedido",
        heading="Panel Interno Verificado",
        subtitle="Validacion superada correctamente.",
        badge="Gateway",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
    {
        "id": "011",
        "name": "Command Execution GET",
        "type": "HARD - WEB",
        "port_web": 8011,
        "default_flag": "EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}",
        "extra_apt": "",
        "extra_env": "",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/flag.txt && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/ui.py /app/global.css /app/flag.txt"
        ),
        "script": """
import html
import os
import subprocess

from flask import Flask, request
from waitress import serve

from ui import register_challenge_ui, render_page

app = Flask(__name__)
register_challenge_ui(app)


@app.route("/")
def index():
    cmd = request.args.get("cmd")
    if cmd:
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            out = html.escape(result.stdout)
        except subprocess.TimeoutExpired:
            out = "Command timed out"
        body = f'<pre class="ctf-output">{out}</pre>'
        return render_page(
            title="Consola de Depuracion",
            heading="Consola Administrativa",
            subtitle="Salida de ejecucion remota.",
            badge="Debug Console",
            body_html=body,
            wide=True,
        )

    body = '<p class="ctf-muted">Uso esperado: ?cmd=whoami</p>'
    return render_page(
        title="Consola de Depuracion",
        heading="Consola Administrativa",
        subtitle="Interfaz de diagnostico por parametro GET.",
        badge="Debug Console",
        body_html=body,
    )


if __name__ == "__main__":
    serve(app, host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8000")), threads=4)
""",
    },
]

DOCKERFILE_TEMPLATE = """FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    HOST=0.0.0.0 \\
    PORT=8000

__EXTRA_APT____EXTRA_ENV__RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='__DEFAULT_FLAG__'

WORKDIR /app
COPY app.py ui.py global.css /app/

__BUILD_STEPS__

USER ctf

EXPOSE 8000

CMD ["python3", "app.py"]
"""


def render_dockerfile(challenge: dict) -> str:
    """Render an isolated, non-root, read-only compatible challenge Dockerfile."""
    return (
        DOCKERFILE_TEMPLATE
        .replace("__EXTRA_APT__", challenge["extra_apt"])
        .replace("__EXTRA_ENV__", challenge["extra_env"])
        .replace("__DEFAULT_FLAG__", challenge["default_flag"])
        .replace("__BUILD_STEPS__", challenge["build_steps"])
    )


def render_service_entry(
    challenge_id: str,
    port_host: int,
    port_container: int,
    default_flag: str,
    mem_limit: str = "128m",
    cpus: str = "0.50",
    pids_limit: int = 64,
    cap_add_net_raw: bool = False,
) -> str:
    """Render a resource-bounded, hardened docker-compose service block."""
    env_var = f"FLAG_WEB_{challenge_id}"
    lines = [
        f"  web-{challenge_id}:",
        "    build:",
        f"      context: ./challenge-web-{challenge_id}",
        "      args:",
        f"        CHALLENGE_FLAG: ${{{env_var}:-{default_flag}}}",
        f"    container_name: ctf-web-{challenge_id}",
        "    restart: unless-stopped",
        "    read_only: true",
        "    tmpfs:",
        '      - "/tmp:rw,noexec,nosuid,size=16m"',
        "    security_opt:",
        '      - "no-new-privileges:true"',
        "    cap_drop:",
        "      - ALL",
    ]
    if cap_add_net_raw:
        lines.extend(["    cap_add:", "      - NET_RAW"])
    lines.extend(
        [
            f"    mem_limit: {mem_limit}",
            f"    memswap_limit: {mem_limit}",
            f"    cpus: {cpus}",
            f"    pids_limit: {pids_limit}",
            "    ports:",
            f'      - "{port_host}:{port_container}"',
            "    networks:",
            "      - ctf-net",
        ]
    )
    return "\n".join(lines) + "\n"


def generate_challenges(base_dir: Path) -> None:
    """Write isolated standalone challenges and hardened docker-compose.yml."""
    css_content = GLOBAL_CSS_SRC.read_text(encoding="utf-8")
    ui_content = UI_PY_SRC.read_text(encoding="utf-8")

    ch001_dir = base_dir / "challenge-web-001"
    ch001_dir.mkdir(parents=True, exist_ok=True)
    (ch001_dir / "index.html").write_text(HTML_001, encoding="utf-8", newline="\n")
    (ch001_dir / "global.css").write_text(css_content, encoding="utf-8", newline="\n")
    (ch001_dir / "nginx.conf").write_text(NGINX_CONF_001, encoding="utf-8", newline="\n")
    (ch001_dir / "Dockerfile").write_text(DOCKERFILE_001, encoding="utf-8", newline="\n")

    service_blocks = [
        render_service_entry(
            "001",
            8001,
            8080,
            "EclipSec{h1dd3n_1n_pl41n_s1ght}",
            mem_limit="64m",
            cpus="0.25",
            pids_limit=32,
        )
    ]

    for challenge in CHALLENGES:
        ch_dir = base_dir / f"challenge-web-{challenge['id']}"
        ch_dir.mkdir(parents=True, exist_ok=True)
        (ch_dir / "app.py").write_text(
            challenge["script"].strip() + "\n", encoding="utf-8", newline="\n"
        )
        (ch_dir / "ui.py").write_text(ui_content, encoding="utf-8", newline="\n")
        (ch_dir / "global.css").write_text(css_content, encoding="utf-8", newline="\n")
        (ch_dir / "Dockerfile").write_text(
            render_dockerfile(challenge), encoding="utf-8", newline="\n"
        )
        service_blocks.append(
            render_service_entry(
                challenge["id"],
                challenge["port_web"],
                8000,
                challenge["default_flag"],
                cap_add_net_raw=(challenge["id"] == "004"),
            )
        )

    compose_content = (
        "services:\n"
        + "\n".join(service_blocks)
        + "\nnetworks:\n  ctf-net:\n    driver: bridge\n"
    )
    (base_dir / "docker-compose.yml").write_text(
        compose_content, encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate_challenges(BASE_DIR)
    print("Challenge directories and docker-compose.yml generated.")
