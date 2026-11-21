FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='EclipSec{h34d3rs_c4n_b3_sp00f3d}'

WORKDIR /app
COPY app.py ui.py global.css /app/

RUN printf '%s\n' "$CHALLENGE_FLAG" > /app/.flag && \
    chown -R root:ctf /app && \
    chmod 550 /app && \
    chmod 440 /app/app.py /app/ui.py /app/global.css /app/.flag

USER ctf

EXPOSE 8000

CMD ["python3", "app.py"]
