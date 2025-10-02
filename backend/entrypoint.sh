#!/bin/sh
# Entrypoint script for the backend service. Waits for the database
# to become available, seeds initial personas, and starts the FastAPI
# application using Uvicorn.

set -e

HOST="${DATABASE_URL##*@}"
HOST="${HOST%%:*}"
PORT="${DATABASE_URL##*:}"
PORT="${PORT%%/*}"

echo "Waiting for database at $HOST:$PORT..."
until nc -z "$HOST" "$PORT"; do
  sleep 1
done
echo "Database is up. Running database seeding..."

# Seed the database with everything needed for demo. Ignore errors in case it has already been seeded.
cd /app && python -m brs_backend.seed_personas || true

echo "Starting backend service..."
uvicorn brs_backend.main:app --host 0.0.0.0 --port 8000 --workers 1
