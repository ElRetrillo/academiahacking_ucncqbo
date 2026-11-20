from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CHALLENGES = [
    {
        "id": "002",
        "name": "Robots & Crawlers",
        "type": "EASY - WEB",
        "port_web": 8002,
        "default_flag": "EclipSec{r0b0ts_4r3_y0ur_fr13nd5}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
from pathlib import Path
from flask import Flask

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome to SecureCorp</h1><p>Nothing to see here.</p></body></html>'


@app.route('/robots.txt')
def robots():
    return 'User-agent: *\\nDisallow: /secret_flag_dir_991'


@app.route('/secret_flag_dir_991')
def flag():
    return read_flag()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "003",
        "name": "Cookie Tampering",
        "type": "EASY - WEB",
        "port_web": 8003,
        "default_flag": "EclipSec{c00k13_m0nst3r_m4n1pul4t10n}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
from pathlib import Path
from flask import Flask, request, make_response

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    role = request.cookies.get('role', 'guest')
    if role == 'admin':
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>{read_flag()}</p></body></html>'
    resp = make_response('<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Guest!</h1><p>You are not an admin.</p></body></html>')
    resp.set_cookie('role', 'guest')
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "004",
        "name": "Ping of Death",
        "type": "MEDIUM - WEB",
        "port_web": 8004,
        "default_flag": "EclipSec{p1ng_0f_d34th_cmdi}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/flag.txt && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/flag.txt"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
import subprocess
from flask import Flask, request, render_template_string

app = Flask(__name__)

template = '''
<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
<h1>Network Diagnostic Tool</h1>
<form method="POST">
    <label>IP to ping:</label>
    <input type="text" name="ip" value="127.0.0.1">
    <button type="submit">Ping</button>
</form>
<pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{{ output }}</pre>
</body></html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        try:
            # Intentional command injection vulnerability for CTF training
            result = subprocess.run(
                f'ping -c 1 {ip}',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=10,
            )
            output = result.stdout
        except subprocess.TimeoutExpired:
            output = 'Command timed out'
    return render_template_string(template, output=output)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "005",
        "name": "LFI to RCE",
        "type": "MEDIUM - WEB",
        "port_web": 8005,
        "default_flag": "EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}",
        "build_steps": (
            "RUN printf '%s\\n' 'Welcome to the home page.' > /app/home.txt && \\\n"
            "    printf '%s\\n' \"$CHALLENGE_FLAG\" > /flag.txt && \\\n"
            "    chown -R root:ctf /app /flag.txt && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/home.txt /flag.txt"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
import html
from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def index():
    file_path = request.args.get('file', 'home.txt')
    try:
        # Intentional local file inclusion vulnerability for CTF training
        with open(file_path, 'r', encoding='utf-8', errors='replace') as fh:
            content = html.escape(fh.read())
    except Exception:
        content = 'File not found'
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>LFI Challenge</h1><p><a href="?file=home.txt" style="color:white;">Home</a></p><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{content}</pre></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "006",
        "name": "SQLi Login Bypass",
        "type": "MEDIUM - WEB",
        "port_web": 8006,
        "default_flag": "EclipSec{sql1_byp4ss_l0g1n}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown ctf:ctf /app && \\\n"
            "    chmod 700 /app && \\\n"
            "    chown root:ctf /app/app.py /app/.flag && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
import sqlite3
from contextlib import closing
from pathlib import Path
from flask import Flask, request, render_template_string

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"
FLAG_PATH = BASE_DIR / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
        count = c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'").fetchone()[0]
        if count == 0:
            c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
        conn.commit()


template = '''
<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
<h1>Admin Login</h1>
<form method="POST">
    <input type="text" name="user" placeholder="Username"><br><br>
    <input type="password" name="pass" placeholder="Password"><br><br>
    <button type="submit">Login</button>
</form>
<p style="color:red">{{ error }}</p>
</body></html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    error = ''
    if request.method == 'POST':
        u = request.form.get('user', '')
        p = request.form.get('pass', '')
        with closing(sqlite3.connect(DB_PATH)) as conn:
            c = conn.cursor()
            # Intentional SQL injection vulnerability for CTF training
            query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
            try:
                c.execute(query)
                if c.fetchone():
                    return render_template_string(
                        '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>{{ flag }}</p></body></html>',
                        flag=read_flag(),
                    )
                error = 'Invalid credentials'
            except Exception as e:
                error = str(e)
    return render_template_string(template, error=error)


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "007",
        "name": "IDOR Profiles",
        "type": "MEDIUM - WEB",
        "port_web": 8007,
        "default_flag": "EclipSec{1d0r_c4n_b3_d4ng3r0us}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
from pathlib import Path
from flask import Flask, request

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    profiles = {
        "1": "Alice - Normal User",
        "2": "Bob - Normal User",
        "0": f"Admin - {read_flag()}",
    }
    uid = request.args.get('id', '1')
    profile = profiles.get(uid, "User not found")
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>User Profile</h1><p>{profile}</p><a href="?id=1" style="color:white;">View Alice</a> | <a href="?id=2" style="color:white;">View Bob</a></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "008",
        "name": "Server-Side Template Injection",
        "type": "HARD - WEB",
        "port_web": 8008,
        "default_flag": "EclipSec{sst1_t3mpl4t3_1nj3ct10n}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c \'cd /app && FLAG="$(cat /app/.flag)" && export FLAG && exec python3 app.py\' &',
        "script": """
from flask import Flask, request, render_template_string

app = Flask(__name__)


@app.route('/')
def index():
    name = request.args.get('name', 'Guest')
    # Intentional SSTI vulnerability for CTF training
    template = f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome {name}!</h1><p>Try to find the flag in the environment variables or files.</p></body></html>'
    return render_template_string(template)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "009",
        "name": "Source Code Leak",
        "type": "EASY - WEB",
        "port_web": 8009,
        "default_flag": "EclipSec{b4ckup_f1l3s_4r3_l34ks}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
from pathlib import Path
from flask import Flask

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    return '''
    <html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
    <h1>Secure Login System</h1>
    <p>Everything is secure here. Definitely no backup files left on the server.</p>
    </body></html>
    '''


@app.route('/index.bak')
def bak():
    return f'''
# Backup file
def login():
    password = "{read_flag()}"
'''


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "010",
        "name": "Headers Matter",
        "type": "MEDIUM - WEB",
        "port_web": 8010,
        "default_flag": "EclipSec{h34d3rs_c4n_b3_sp00f3d}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/.flag && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/.flag"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
from pathlib import Path
from flask import Flask, request

app = Flask(__name__)
FLAG_PATH = Path(__file__).resolve().parent / ".flag"


def read_flag() -> str:
    if FLAG_PATH.exists():
        return FLAG_PATH.read_text(encoding="utf-8").strip()
    return ""


@app.route('/')
def index():
    ua = request.headers.get('User-Agent', '')
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    client_ip = forwarded_for.split(',')[0].strip() if forwarded_for else (request.remote_addr or '')

    if 'SecureBrowser1.0' not in ua:
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only SecureBrowser1.0 is allowed.</p></body></html>'

    if client_ip != '127.0.0.1':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only local connections (127.0.0.1) are allowed.</p></body></html>'

    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Granted!</h1><p>{read_flag()}</p></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
    {
        "id": "011",
        "name": "Command Execution GET",
        "type": "HARD - WEB",
        "port_web": 8011,
        "default_flag": "EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}",
        "build_steps": (
            "RUN printf '%s\\n' \"$CHALLENGE_FLAG\" > /app/flag.txt && \\\n"
            "    chown -R root:ctf /app && \\\n"
            "    chmod 550 /app && \\\n"
            "    chmod 440 /app/app.py /app/flag.txt"
        ),
        "launch_cmd": 'su -s /bin/sh ctf -c "cd /app && exec python3 app.py" &',
        "script": """
import html
import subprocess
from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def index():
    cmd = request.args.get('cmd')
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
            out = 'Command timed out'
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{out}</pre></body></html>'
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Admin Debug Console</h1><p>Usage: ?cmd=whoami</p></body></html>'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""",
    },
]

DOCKERFILE_TEMPLATE = """FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \\
    nginx \\
    ca-certificates \\
    bash \\
    python3 \\
    python3-pip \\
    iputils-ping \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir flask

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='__DEFAULT_FLAG__'

RUN mkdir -p /app
COPY app.py /app/app.py

__BUILD_STEPS__

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

__LAUNCH_CMD__

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chown root:root /usr/local/sbin/start.sh && chmod 700 /usr/local/sbin/start.sh

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
"""


def render_dockerfile(challenge: dict) -> str:
    """Render an isolated, non-root standalone challenge Dockerfile."""
    return (
        DOCKERFILE_TEMPLATE
        .replace("__DEFAULT_FLAG__", challenge["default_flag"])
        .replace("__BUILD_STEPS__", challenge["build_steps"])
        .replace("__LAUNCH_CMD__", challenge["launch_cmd"])
    )


def render_service_entry(challenge_id: str, port_web: int, default_flag: str) -> str:
    """Render a docker-compose service block with parameterized flag build-arg."""
    env_var = f"FLAG_WEB_{challenge_id}"
    return (
        f"  web-{challenge_id}:\n"
        f"    build:\n"
        f"      context: ./challenge-web-{challenge_id}\n"
        f"      args:\n"
        f"        CHALLENGE_FLAG: ${{{env_var}:-{default_flag}}}\n"
        f"    container_name: ctf-web-{challenge_id}\n"
        f"    restart: unless-stopped\n"
        f"    ports:\n"
        f"      - \"{port_web}:80\"\n"
        f"    networks:\n"
        f"      - ctf-net\n"
    )


def generate_challenges(base_dir: Path) -> None:
    """Write isolated standalone challenges and an idempotent docker-compose.yml."""
    service_blocks = [
        render_service_entry("001", 8001, "EclipSec{h1dd3n_1n_pl41n_s1ght}")
    ]

    for challenge in CHALLENGES:
        ch_dir = base_dir / f"challenge-web-{challenge['id']}"
        ch_dir.mkdir(parents=True, exist_ok=True)
        (ch_dir / "app.py").write_text(
            challenge["script"].strip() + "\n", encoding="utf-8", newline="\n"
        )
        (ch_dir / "Dockerfile").write_text(
            render_dockerfile(challenge), encoding="utf-8", newline="\n"
        )
        service_blocks.append(
            render_service_entry(
                challenge["id"], challenge["port_web"], challenge["default_flag"]
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
