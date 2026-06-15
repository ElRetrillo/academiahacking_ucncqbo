import os
import shutil

base_dir = "/home/daniel/academiahacking_ucncqbo/docker"
mono_dir = os.path.join(base_dir, "monolithic")
os.makedirs(mono_dir, exist_ok=True)

# Generate HTML and CSS for web-001
web_001_dir = os.path.join(mono_dir, "web-001")
os.makedirs(web_001_dir, exist_ok=True)

html_001 = '''<!DOCTYPE html>
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
</html>'''

css_001 = '''body { background: radial-gradient(circle at center, #1a1a2e 0%, #16213e 100%); color: #e94560; font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; } .login-card { background: rgba(22, 33, 62, 0.8); backdrop-filter: blur(10px); padding: 2.5rem; border-radius: 15px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8); border: 1px solid rgba(233, 69, 96, 0.2); width: 100%; max-width: 400px; text-align: center; animation: fadeIn 0.8s ease-out; } @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } } h1 { margin-bottom: 1.5rem; font-weight: 300; letter-spacing: 2px; text-transform: uppercase; } .input-group { margin-bottom: 1rem; text-align: left; } label { display: block; margin-bottom: 0.5rem; font-size: 0.8rem; opacity: 0.8; } input { width: 100%; padding: 0.8rem; background: #0f3460; border: 1px solid #16213e; border-radius: 5px; color: white; outline: none; transition: border 0.3s; } input:focus { border: 1px solid #e94560; } button { width: 100%; padding: 1rem; background: #e94560; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; text-transform: uppercase; transition: 0.3s; margin-top: 1rem; } button:hover { background: #ff2e63; box-shadow: 0 0 15px rgba(233, 69, 96, 0.4); } .footer { margin-top: 1.5rem; font-size: 0.7rem; opacity: 0.5; }'''

with open(os.path.join(web_001_dir, "index.html"), "w") as f: f.write(html_001)
with open(os.path.join(web_001_dir, "style.css"), "w") as f: f.write(css_001)

nginx_blocks = []
start_cmds = []

# Nginx config for web-001
nginx_blocks.append('''
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
''')
start_cmds.append('ttyd --port 7681 --writable --cwd /root -t title="CTF Shell" --base-path /web-001/ws bash &')

# Process apps 002 to 011
for i in range(2, 12):
    ch = f"00{i}" if i < 10 else f"0{i}"
    ch_name = f"challenge-web-{ch}"
    src = os.path.join(base_dir, ch_name, "app.py")
    dst_dir = os.path.join(mono_dir, f"web-{ch}")
    os.makedirs(dst_dir, exist_ok=True)
    
    port_web = 8000 + i
    port_ttyd = 7680 + i
    
    with open(src, 'r') as f:
        content = f.read()
        
    # Replace port
    content = content.replace("port=8000", f"port={port_web}")
    # Replace flag names to avoid overwriting
    content = content.replace("/flag.txt", f"/flag_web{ch}.txt")
    
    with open(os.path.join(dst_dir, "app.py"), "w") as f:
        f.write(content)
        
    # Nginx blocks and start commands
    nginx_blocks.append(f'''
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
''')
    start_cmds.append(f'cd /app/web-{ch} && python3 app.py &')
    start_cmds.append(f'ttyd --port {port_ttyd} --writable --cwd /root -t title="CTF Shell" --base-path /web-{ch}/ws bash &')

# Create start.sh
start_sh = '''#!/bin/bash
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
''' + "".join(nginx_blocks) + '''
}
NGINXCONF

nginx -t

''' + "\n".join(start_cmds) + '''

echo "All services started."
exec nginx -g "daemon off;"
'''

with open(os.path.join(mono_dir, "start.sh"), "w") as f:
    f.write(start_sh)

# Create Dockerfile
dockerfile = '''FROM ubuntu:22.04
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

COPY . /app
RUN chmod +x /app/start.sh

# Web-005 files setup
RUN echo 'Welcome to the home page.' > /app/web-005/home.txt

EXPOSE 80

CMD ["/app/start.sh"]
'''

with open(os.path.join(mono_dir, "Dockerfile"), "w") as f:
    f.write(dockerfile)

print("Monolithic container setup complete in docker/monolithic/")
