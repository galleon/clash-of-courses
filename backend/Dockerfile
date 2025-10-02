FROM python:3.11-slim

# Install system dependencies
# Use netcat-openbsd to provide the `nc` command. The generic
# `netcat` virtual package isn't available on some Debian variants.
RUN apt-get update && apt-get install -y netcat-openbsd gcc && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy application code first
COPY brs_backend/ brs_backend/
COPY tests/ tests/
COPY pyproject.toml .
COPY README.md .
COPY entrypoint.sh .

# Install the package and dependencies with uv
RUN uv pip install --system -e .

# Copy entrypoint script
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
