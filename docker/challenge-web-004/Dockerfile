FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='EclipSec{p1ng_0f_d34th_cmdi}'

WORKDIR /app
COPY app.py ui.py global.css /app/

RUN printf '%s\n' "$CHALLENGE_FLAG" > /app/flag.txt && \
    chown -R root:ctf /app && \
    chmod 550 /app && \
    chmod 440 /app/app.py /app/ui.py /app/global.css /app/flag.txt

USER ctf

EXPOSE 8000

CMD ["python3", "app.py"]
