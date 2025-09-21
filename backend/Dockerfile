FROM python:3.11-slim

# Install system dependencies
# Use netcat-openbsd to provide the `nc` command. The generic
# `netcat` virtual package isn't available on some Debian variants.
RUN apt-get update && apt-get install -y netcat-openbsd gcc && rm -rf /var/lib/apt/lists/*

# Install uv and python dependencies
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy requirements and install via uv into the system environment
COPY requirements.txt .
RUN uv pip install --no-cache-dir --system -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]