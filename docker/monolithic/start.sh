#!/bin/bash
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

    location /web-001/ {
        alias /app/web-001/;
        index index.html;
    }

    location /web-002/ {
        proxy_pass http://127.0.0.1:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-003/ {
        proxy_pass http://127.0.0.1:8003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-004/ {
        proxy_pass http://127.0.0.1:8004/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-005/ {
        proxy_pass http://127.0.0.1:8005/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-006/ {
        proxy_pass http://127.0.0.1:8006/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-007/ {
        proxy_pass http://127.0.0.1:8007/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-008/ {
        proxy_pass http://127.0.0.1:8008/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-009/ {
        proxy_pass http://127.0.0.1:8009/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-010/ {
        proxy_pass http://127.0.0.1:8010/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /web-011/ {
        proxy_pass http://127.0.0.1:8011/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

}
NGINXCONF

nginx -t

su -s /bin/sh web002 -c "cd /app/web-002 && exec python3 app.py" &
su -s /bin/sh web003 -c "cd /app/web-003 && exec python3 app.py" &
su -s /bin/sh web004 -c "cd /app/web-004 && exec python3 app.py" &
su -s /bin/sh web005 -c "cd /app/web-005 && exec python3 app.py" &
su -s /bin/sh web006 -c "cd /app/web-006 && exec python3 app.py" &
su -s /bin/sh web007 -c "cd /app/web-007 && exec python3 app.py" &
su -s /bin/sh web008 -c 'cd /app/web-008 && FLAG="$(cat /app/web-008/.flag)" && export FLAG && exec python3 app.py' &
su -s /bin/sh web009 -c "cd /app/web-009 && exec python3 app.py" &
su -s /bin/sh web010 -c "cd /app/web-010 && exec python3 app.py" &
su -s /bin/sh web011 -c "cd /app/web-011 && exec python3 app.py" &

echo "All services started."
exec nginx -g "daemon off;"
