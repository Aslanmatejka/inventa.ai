# Backend Dockerfile for inventa.ai
# Build:   docker build -t inventa-backend -f Backend/Dockerfile .
# Run:     docker run -p 3001:3001 --env-file .env inventa-backend
FROM python:3.12-slim

# System deps needed by CadQuery / OCP
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    libsm6 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY Backend/requirements.txt /app/Backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/Backend/requirements.txt

# Copy the rest of the backend
COPY Backend /app/Backend
COPY migrations /app/migrations

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
ENV PORT=3001

EXPOSE 3001

WORKDIR /app/Backend

# Render / Docker health check hits /api/healthz
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://127.0.0.1:${PORT}/api/healthz', timeout=3); sys.exit(0)" || exit 1

CMD ["python", "start.py"]
