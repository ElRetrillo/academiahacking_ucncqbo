FROM nginx:1.27-alpine

ARG CHALLENGE_FLAG='EclipSec{h1dd3n_1n_pl41n_s1ght}'

ENV PORT=8080

COPY docker/challenge-web-001/nginx.conf /etc/nginx/nginx.conf
COPY docker/challenge-web-001/index.html /usr/share/nginx/html/index.html
COPY docker/shared/global.css /usr/share/nginx/html/global.css

RUN awk 'BEGIN { flag = ENVIRON["CHALLENGE_FLAG"] } { idx = index($0, "__CHALLENGE_FLAG__"); if (idx > 0) { $0 = substr($0, 1, idx - 1) flag substr($0, idx + 18) } print }' /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp && \
    mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html && \
    chown -R root:nginx /usr/share/nginx/html && \
    chmod 550 /usr/share/nginx/html && \
    chmod 440 /usr/share/nginx/html/index.html /usr/share/nginx/html/global.css

USER nginx

EXPOSE 8080

ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
