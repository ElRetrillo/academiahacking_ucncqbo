FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# Explicitly expose 8000 and bind to 8000. Railway will read EXPOSE 8000 and route to it.
EXPOSE 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
