# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH=/app/src \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==2.3.0

# Copy Poetry files first (better layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no venv, no root package install)
RUN poetry install --only main --no-root --no-ansi \
 && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run API (Celery containers override this command)
CMD ["uvicorn", "vibeify_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
