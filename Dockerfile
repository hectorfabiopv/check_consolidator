FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# dependencias del sistema (si necesitas, p. ej., build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8080

# Escucha el puerto de la variable PORT si está disponible (Cloud Run usa $PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
