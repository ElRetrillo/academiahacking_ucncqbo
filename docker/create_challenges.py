import os

challenges = [
    {
        "id": "002",
        "name": "Robots & Crawlers",
        "type": "EASY - WEB",
        "desc": "Check the robots.txt file.",
        "port_web": 8002,
        "port_ttyd": 7682,
        "script": """
import os
from flask import Flask, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome to SecureCorp</h1><p>Nothing to see here.</p></body></html>'

@app.route('/robots.txt')
def robots():
    return 'User-agent: *\\nDisallow: /secret_flag_dir_991'

@app.route('/secret_flag_dir_991')
def flag():
    return 'EclipSec{r0b0ts_4r3_y0ur_fr13nd5}'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "003",
        "name": "Cookie Tampering",
        "type": "EASY - WEB",
        "desc": "Manipulate your cookie to become admin.",
        "port_web": 8003,
        "port_ttyd": 7683,
        "script": """
from flask import Flask, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    role = request.cookies.get('role', 'guest')
    if role == 'admin':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>EclipSec{c00k13_m0nst3r_m4n1pul4t10n}</p></body></html>'
    else:
        resp = make_response('<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Guest!</h1><p>You are not an admin.</p></body></html>')
        resp.set_cookie('role', 'guest')
        return resp

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "004",
        "name": "Ping of Death",
        "type": "MEDIUM - WEB",
        "desc": "Command Injection in a ping tool.",
        "port_web": 8004,
        "port_ttyd": 7684,
        "script": """
import os
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
        # VULNERABLE
        output = os.popen(f'ping -c 1 {ip}').read()
    return render_template_string(template, output=output)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "005",
        "name": "LFI to RCE",
        "type": "MEDIUM - WEB",
        "desc": "Local File Inclusion.",
        "port_web": 8005,
        "port_ttyd": 7685,
        "script": """
import os
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    file = request.args.get('file', 'home.txt')
    try:
        # VULNERABLE
        content = open(file).read()
    except:
        content = 'File not found'
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>LFI Challenge</h1><p><a href="?file=home.txt" style="color:white;">Home</a></p><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{content}</pre></body></html>'

if __name__ == '__main__':
    with open('home.txt', 'w') as f: f.write('Welcome to the home page.')
    with open('/flag.txt', 'w') as f: f.write('EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}')
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "006",
        "name": "SQLi Login Bypass",
        "type": "MEDIUM - WEB",
        "desc": "Bypass the login with SQL Injection.",
        "port_web": 8006,
        "port_ttyd": 7686,
        "script": """
import sqlite3
from flask import Flask, request, render_template_string
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
    c.execute("INSERT INTO users VALUES ('admin', 'super_secret_password_123!')")
    conn.commit()
    conn.close()

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
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        # VULNERABLE
        query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        try:
            c.execute(query)
            if c.fetchone():
                return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome Admin!</h1><p>EclipSec{sql1_byp4ss_l0g1n}</p></body></html>'
            else:
                error = 'Invalid credentials'
        except Exception as e:
            error = str(e)
    return render_template_string(template, error=error)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "007",
        "name": "IDOR Profiles",
        "type": "MEDIUM - WEB",
        "desc": "Insecure Direct Object Reference.",
        "port_web": 8007,
        "port_ttyd": 7687,
        "script": """
from flask import Flask, request
app = Flask(__name__)

profiles = {
    "1": "Alice - Normal User",
    "2": "Bob - Normal User",
    "0": "Admin - EclipSec{1d0r_c4n_b3_d4ng3r0us}"
}

@app.route('/')
def index():
    uid = request.args.get('id', '1')
    profile = profiles.get(uid, "User not found")
    return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>User Profile</h1><p>{profile}</p><a href="?id=1" style="color:white;">View Alice</a> | <a href="?id=2" style="color:white;">View Bob</a></body></html>'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "008",
        "name": "Server-Side Template Injection",
        "type": "HARD - WEB",
        "desc": "SSTI vulnerability.",
        "port_web": 8008,
        "port_ttyd": 7688,
        "script": """
from flask import Flask, request, render_template_string
app = Flask(__name__)

@app.route('/')
def index():
    name = request.args.get('name', 'Guest')
    # VULNERABLE
    template = f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Welcome {name}!</h1><p>Try to find the flag in the environment variables or files.</p></body></html>'
    return render_template_string(template)

if __name__ == '__main__':
    import os
    os.environ['FLAG'] = 'EclipSec{sst1_t3mpl4t3_1nj3ct10n}'
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "009",
        "name": "Source Code Leak",
        "type": "EASY - WEB",
        "desc": "Check for backup files.",
        "port_web": 8009,
        "port_ttyd": 7689,
        "script": """
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;">
    <h1>Secure Login System</h1>
    <p>Everything is secure here. Definitely no backup files left on the server.</p>
    </body></html>
    '''

@app.route('/index.py.bak')
def bak():
    return '''
# Backup file
def login():
    password = "EclipSec{b4ckup_f1l3s_4r3_l34ks}"
    # TODO: Implement database auth
'''

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "010",
        "name": "Headers Matter",
        "type": "MEDIUM - WEB",
        "desc": "Spoof your headers.",
        "port_web": 8010,
        "port_ttyd": 7690,
        "script": """
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    ua = request.headers.get('User-Agent', '')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if 'SecureBrowser1.0' not in ua:
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only SecureBrowser1.0 is allowed.</p></body></html>'
    
    if ip != '127.0.0.1':
        return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Denied</h1><p>Only local connections (127.0.0.1) are allowed.</p></body></html>'
        
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Access Granted!</h1><p>EclipSec{h34d3rs_c4n_b3_sp00f3d}</p></body></html>'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
"""
    },
    {
        "id": "011",
        "name": "Command Execution GET",
        "type": "HARD - WEB",
        "desc": "Execute commands via GET parameter.",
        "port_web": 8011,
        "port_ttyd": 7691,
        "script": """
import os
from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def index():
    cmd = request.args.get('cmd')
    if cmd:
        # VULNERABLE
        out = os.popen(cmd).read()
        return f'<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><pre style="text-align:left; background:#0f3460; padding:20px; color:white;">{out}</pre></body></html>'
    return '<html><body style="background:#1a1a2e;color:#e94560;font-family:sans-serif;text-align:center;padding:50px;"><h1>Admin Debug Console</h1><p>Usage: ?cmd=whoami</p></body></html>'

if __name__ == '__main__':
    with open('/flag.txt', 'w') as f: f.write('EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}')
    app.run(host='127.0.0.1', port=8000)
"""
    }
]

dockerfile_template = '''\\
# ================================================================
# Reto CTF de EclipSec
# ================================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \\
    nginx \\
    curl \\
    wget \\
    ca-certificates \\
    bash \\
    procps \\
    net-tools \\
    python3 \\
    python3-pip \\
    iputils-ping \\
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

# Instalar ttyd
RUN ARCH=$(uname -m) && \\
    if [ "$ARCH" = "x86_64" ]; then TTYD_ARCH="x86_64"; \\
    elif [ "$ARCH" = "aarch64" ]; then TTYD_ARCH="aarch64"; \\
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \\
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.${TTYD_ARCH}" \\
        -o /usr/local/bin/ttyd && \\
    chmod +x /usr/local/bin/ttyd

# Script del reto
RUN mkdir -p /app
COPY app.py /app/app.py

# Nginx
RUN cat > /start.sh << 'STARTSCRIPT'
#!/bin/bash
set -e

cat > /etc/nginx/sites-available/default << 'NGINXCONF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \\$host;
    }
}
NGINXCONF

nginx -t

ttyd \\
    --port 7681 \\
    --writable \\
    --cwd /root \\
    -t title="CTF Shell" \\
    --base-path /ws \\
    bash &

cd /app && python3 app.py &

exec nginx -g "daemon off;"
STARTSCRIPT
RUN chmod +x /start.sh

EXPOSE 80 7681

CMD ["/start.sh"]
'''

base_dir = "/home/daniel/academiahacking_ucncqbo/docker"
compose_additions = ""

for c in challenges:
    ch_dir = os.path.join(base_dir, f"challenge-web-{c['id']}")
    os.makedirs(ch_dir, exist_ok=True)
    
    with open(os.path.join(ch_dir, "app.py"), "w") as f:
        f.write(c["script"].strip())
    
    with open(os.path.join(ch_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_template)
        
    compose_additions += f"""
  # ──────────────────────────────────────────────────────────────
  # web-{c['id']}: {c['name']} ({c['type']})
  # ──────────────────────────────────────────────────────────────
  web-{c['id']}:
    build: ./challenge-web-{c['id']}
    container_name: ctf-web-{c['id']}
    restart: unless-stopped
    ports:
      - "{c['port_web']}:80"
      - "{c['port_ttyd']}:7681"
    networks:
      - ctf-net
"""

# Append to docker-compose.yml
compose_path = os.path.join(base_dir, "docker-compose.yml")
with open(compose_path, "r") as f:
    original_compose = f.read()

# Insert before `networks:`
if "networks:" in original_compose:
    parts = original_compose.split("networks:", 1)
    new_compose = parts[0] + compose_additions + "\\nnetworks:" + parts[1]
    with open(compose_path, "w") as f:
        f.write(new_compose)
else:
    with open(compose_path, "a") as f:
        f.write(compose_additions)

print("Created 10 new challenges and updated docker-compose.yml successfully.")
