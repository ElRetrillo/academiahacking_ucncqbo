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

# Copy only the monolithic directory contents to /app
# Railway build context is the repo root, so we need the full path
COPY docker/monolithic/ /app/
RUN chmod +x /app/start.sh

# Web-005 files setup
RUN echo 'Welcome to the home page.' > /app/web-005/home.txt

# Web-005 and Web-011 flag files
RUN echo 'EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}' > /flag_web005.txt && \
    echo 'EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}' > /flag_web011.txt

EXPOSE 80

CMD ["/app/start.sh"]
