# syntax=docker/dockerfile:1.4
FROM python:3.11-slim-bookworm AS base

# Set environment variables for optimal Python behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_NO_CACHE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install uv

WORKDIR /app

# Build arg: whether to install dev extras (defaults to true for dev images)
ARG INSTALL_DEV=true

# Copy dependency files first for better layer caching
COPY pyproject.toml README.md langgraph.json ./

# Install dependencies with BuildKit cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    sh -c 'set -e; if [ "$INSTALL_DEV" = "true" ]; then EXTRAS="[dev]"; else EXTRAS=""; fi; uv pip install --system -e ".${EXTRAS}"'

# Copy application code
COPY agent/ ./agent/
COPY cli/ ./cli/
COPY infra/ ./infra/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash agent && \
    chown -R agent:agent /app
USER agent

EXPOSE 40003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:40003/threads -X POST -H "Content-Type: application/json" -d '{}' || exit 1

CMD ["python", "-m", "cli.agent", "serve", "--port", "40003", "--host", "0.0.0.0"]
