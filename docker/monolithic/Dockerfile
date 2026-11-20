FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx ca-certificates bash python3 python3-pip iputils-ping sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir flask

RUN for uid in 002 003 004 005 006 007 008 009 010 011; do \
        useradd --system --no-create-home --shell /usr/sbin/nologin "web${uid}"; \
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

RUN sed -i 's/\r$//' /usr/local/sbin/start.sh && \
    chown root:root /usr/local/sbin/start.sh && \
    chmod 700 /usr/local/sbin/start.sh

RUN python3 -c "import os, pathlib; p = pathlib.Path('/app/web-001/index.html'); p.write_text(p.read_text(encoding='utf-8').replace('__CHALLENGE_FLAG__', os.environ['FLAG_WEB_001']), encoding='utf-8')" && \
    chown -R root:www-data /app/web-001 && \
    chmod 750 /app/web-001 && \
    chmod 640 /app/web-001/*

RUN printf '%s\n' "$FLAG_WEB_002" > /app/web-002/.flag && \
    printf '%s\n' "$FLAG_WEB_003" > /app/web-003/.flag && \
    printf '%s\n' "$FLAG_WEB_004" > /app/web-004/flag.txt && \
    printf '%s\n' 'Welcome to the home page.' > /app/web-005/home.txt && \
    printf '%s\n' "$FLAG_WEB_005" > /flag.txt && \
    printf '%s\n' "$FLAG_WEB_006" > /app/web-006/.flag && \
    printf '%s\n' "$FLAG_WEB_007" > /app/web-007/.flag && \
    printf '%s\n' "$FLAG_WEB_008" > /app/web-008/.flag && \
    printf '%s\n' "$FLAG_WEB_009" > /app/web-009/.flag && \
    printf '%s\n' "$FLAG_WEB_010" > /app/web-010/.flag && \
    printf '%s\n' "$FLAG_WEB_011" > /app/web-011/flag.txt && \
    for uid in 002 003 004 005 007 008 009 010 011; do \
        chown -R "root:web${uid}" "/app/web-${uid}" && \
        chmod 550 "/app/web-${uid}" && \
        chmod 440 "/app/web-${uid}/"*; \
    done && \
    chown root:web005 /flag.txt && chmod 440 /flag.txt && \
    chown web006:web006 /app/web-006 && chmod 700 /app/web-006 && \
    chown root:web006 /app/web-006/app.py /app/web-006/.flag && \
    chmod 440 /app/web-006/app.py /app/web-006/.flag && \
    chmod 440 /app/web-002/.flag /app/web-003/.flag /app/web-007/.flag /app/web-008/.flag /app/web-009/.flag /app/web-010/.flag

EXPOSE 80

CMD ["/usr/local/sbin/start.sh"]
