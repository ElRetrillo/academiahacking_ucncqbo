FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx curl wget ca-certificates bash procps net-tools \
    python3 python3-pip iputils-ping sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask

RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then TTYD_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then TTYD_ARCH="aarch64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -sSL "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.${TTYD_ARCH}" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

ENV FLAG='EclipSec{sst1_t3mpl4t3_1nj3ct10n}'

COPY docker/monolithic/ /app/
RUN chmod +x /app/start.sh

RUN echo 'Welcome to the home page.' > /app/web-005/home.txt && \
    echo 'EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}' > /flag.txt && \
    cp /flag.txt /app/web-005/flag.txt && \
    echo 'EclipSec{p1ng_0f_d34th_cmdi}' > /flag_web004.txt && \
    cp /flag_web004.txt /app/web-004/flag.txt && \
    echo 'EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}' > /flag_web011.txt && \
    cp /flag_web011.txt /app/web-011/flag.txt

EXPOSE 80

CMD ["/app/start.sh"]
