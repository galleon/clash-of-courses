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
echo "Database is up. Seeding personas..."

# Seed the database. Ignore errors in case it has already been seeded.
python seed_personas.py || true

echo "Starting backend service..."
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1