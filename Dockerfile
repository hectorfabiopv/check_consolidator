# Use una imagen oficial de Python como base
FROM python:3.12-slim

# Setear el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos primero para cachear dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y mariadb-client && rm -rf /var/lib/apt/lists/*

# Copiar el resto del código
COPY app ./app

# Exponer puerto para Cloud Run
EXPOSE 8080

# Variables de entorno por defecto (pueden ser sobrescritas en Cloud Run)
ENV PORT=8080

# Comando por defecto para correr FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
