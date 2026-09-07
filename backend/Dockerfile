FROM python:3.11-slim

WORKDIR /app

# Install git and required utilities for cloning legacy repositories
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app

ENV PYTHONPATH=/app
ENV STORAGE_BASE=/data/nexsolve/projects
ENV VECTOR_STORE_DIR=/data/nexsolve/vector_store

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
