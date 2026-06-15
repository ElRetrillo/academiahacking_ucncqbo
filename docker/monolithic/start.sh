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
    location /web-001/ws/ {
        proxy_pass http://127.0.0.1:7681/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-002/ {
        proxy_pass http://127.0.0.1:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-002/ws/ {
        proxy_pass http://127.0.0.1:7682/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-003/ {
        proxy_pass http://127.0.0.1:8003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-003/ws/ {
        proxy_pass http://127.0.0.1:7683/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-004/ {
        proxy_pass http://127.0.0.1:8004/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-004/ws/ {
        proxy_pass http://127.0.0.1:7684/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-005/ {
        proxy_pass http://127.0.0.1:8005/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-005/ws/ {
        proxy_pass http://127.0.0.1:7685/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-006/ {
        proxy_pass http://127.0.0.1:8006/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-006/ws/ {
        proxy_pass http://127.0.0.1:7686/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-007/ {
        proxy_pass http://127.0.0.1:8007/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-007/ws/ {
        proxy_pass http://127.0.0.1:7687/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-008/ {
        proxy_pass http://127.0.0.1:8008/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-008/ws/ {
        proxy_pass http://127.0.0.1:7688/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-009/ {
        proxy_pass http://127.0.0.1:8009/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-009/ws/ {
        proxy_pass http://127.0.0.1:7689/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-010/ {
        proxy_pass http://127.0.0.1:8010/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-010/ws/ {
        proxy_pass http://127.0.0.1:7690/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /web-011/ {
        proxy_pass http://127.0.0.1:8011/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    location /web-011/ws/ {
        proxy_pass http://127.0.0.1:7691/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

}
NGINXCONF

nginx -t

ttyd --port 7681 --writable --cwd /root -t title="CTF Shell" --base-path /web-001/ws bash &
cd /app/web-002 && python3 app.py &
ttyd --port 7682 --writable --cwd /root -t title="CTF Shell" --base-path /web-002/ws bash &
cd /app/web-003 && python3 app.py &
ttyd --port 7683 --writable --cwd /root -t title="CTF Shell" --base-path /web-003/ws bash &
cd /app/web-004 && python3 app.py &
ttyd --port 7684 --writable --cwd /root -t title="CTF Shell" --base-path /web-004/ws bash &
cd /app/web-005 && python3 app.py &
ttyd --port 7685 --writable --cwd /root -t title="CTF Shell" --base-path /web-005/ws bash &
cd /app/web-006 && python3 app.py &
ttyd --port 7686 --writable --cwd /root -t title="CTF Shell" --base-path /web-006/ws bash &
cd /app/web-007 && python3 app.py &
ttyd --port 7687 --writable --cwd /root -t title="CTF Shell" --base-path /web-007/ws bash &
cd /app/web-008 && python3 app.py &
ttyd --port 7688 --writable --cwd /root -t title="CTF Shell" --base-path /web-008/ws bash &
cd /app/web-009 && python3 app.py &
ttyd --port 7689 --writable --cwd /root -t title="CTF Shell" --base-path /web-009/ws bash &
cd /app/web-010 && python3 app.py &
ttyd --port 7690 --writable --cwd /root -t title="CTF Shell" --base-path /web-010/ws bash &
cd /app/web-011 && python3 app.py &
ttyd --port 7691 --writable --cwd /root -t title="CTF Shell" --base-path /web-011/ws bash &

echo "All services started."
exec nginx -g "daemon off;"
