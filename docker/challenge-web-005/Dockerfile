FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

RUN pip install --no-cache-dir "flask>=3.0.0" "waitress>=3.0.0"

RUN useradd --system --no-create-home --shell /usr/sbin/nologin ctf

ARG CHALLENGE_FLAG='EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}'

WORKDIR /app
COPY docker/challenge-web-005/app.py docker/shared/ui.py docker/shared/global.css /app/

RUN printf '%s\n' 'Welcome to the home page.' > /app/home.txt && \
    printf '%s\n' "$CHALLENGE_FLAG" > /flag.txt && \
    chown -R root:ctf /app /flag.txt && \
    chmod 550 /app && \
    chmod 440 /app/app.py /app/ui.py /app/global.css /app/home.txt /flag.txt

USER ctf

EXPOSE 8000

CMD ["python3", "app.py"]
