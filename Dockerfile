# ============================================
# Dockerfile para SIRUE - Sistema de Objetos Perdidos y Encontrados
# Entorno de producción optimizado para Python 3.12 Slim
# ============================================

FROM python:3.12-slim

# Metadatos de la imagen
LABEL maintainer="Equipo de Arquitectura SIRUE <arquitectura@campus.edu>"
LABEL description="Sistema Digital de Objetos Perdidos y Encontrados para Campus Universitario"

# Evitar escritura de bytecode .pyc y forzar salida stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    SIRUE_HOST=0.0.0.0 \
    SIRUE_PORT=8080 \
    SIRUE_DB_PATH=/app/data/sirue.db \
    SIRUE_UPLOAD_PATH=/app/uploads

WORKDIR /app

# Instalar dependencias del sistema mínimas requeridas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY src/ /app/src/
COPY main.py /app/main.py
COPY pyproject.toml /app/pyproject.toml

# Crear directorios para los volúmenes persistentes y asignar permisos
RUN mkdir -p /app/data /app/uploads && \
    chmod 777 /app/data /app/uploads

# Exponer el puerto del servidor web NiceGUI
EXPOSE 8080

# Chequeo de salud del contenedor
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Comando de inicio del servidor
CMD ["python", "main.py"]
