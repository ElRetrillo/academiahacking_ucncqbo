#!/bin/bash
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

sed -i "s/__PORT__/${LISTEN_PORT}/g" /etc/nginx/sites-available/default

nginx -t

setpriv --reuid=web002 --regid=web002 --clear-groups sh -c "cd /app/web-002 && HOST=127.0.0.1 PORT=8002 exec python3 app.py" &
setpriv --reuid=web003 --regid=web003 --clear-groups sh -c "cd /app/web-003 && HOST=127.0.0.1 PORT=8003 exec python3 app.py" &
setpriv --reuid=web004 --regid=web004 --clear-groups sh -c "cd /app/web-004 && HOST=127.0.0.1 PORT=8004 exec python3 app.py" &
setpriv --reuid=web005 --regid=web005 --clear-groups sh -c "cd /app/web-005 && HOST=127.0.0.1 PORT=8005 exec python3 app.py" &
setpriv --reuid=web006 --regid=web006 --clear-groups sh -c "cd /app/web-006 && HOST=127.0.0.1 PORT=8006 exec python3 app.py" &
setpriv --reuid=web007 --regid=web007 --clear-groups sh -c "cd /app/web-007 && HOST=127.0.0.1 PORT=8007 exec python3 app.py" &
setpriv --reuid=web008 --regid=web008 --clear-groups sh -c "cd /app/web-008 && HOST=127.0.0.1 PORT=8008 exec python3 app.py" &
setpriv --reuid=web009 --regid=web009 --clear-groups sh -c "cd /app/web-009 && HOST=127.0.0.1 PORT=8009 exec python3 app.py" &
setpriv --reuid=web010 --regid=web010 --clear-groups sh -c "cd /app/web-010 && HOST=127.0.0.1 PORT=8010 exec python3 app.py" &
setpriv --reuid=web011 --regid=web011 --clear-groups sh -c "cd /app/web-011 && HOST=127.0.0.1 PORT=8011 exec python3 app.py" &

echo "All services started."
exec nginx -g "daemon off;"
