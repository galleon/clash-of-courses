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
echo "Database is up. Dropping and recreating tables with fresh data..."

# Drop all tables with CASCADE to handle foreign key dependencies
cd /app && python -c "
from brs_backend.models.database import Base
from brs_backend.database.connection import engine
from sqlalchemy import text

print('Dropping all existing tables with CASCADE...')
with engine.connect() as conn:
    # Drop all tables in the public schema with CASCADE
    conn.execute(text('DROP SCHEMA public CASCADE;'))
    conn.execute(text('CREATE SCHEMA public;'))
    conn.commit()

print('Creating fresh tables...')
Base.metadata.create_all(bind=engine)
print('Tables recreated successfully!')
"

# Seed the database with fresh data using SQLAlchemy models
echo "Seeding database with personas and users using SQLAlchemy models..."
echo "- Using models from models/database.py for schema consistency"
echo "- Seeding personas (students, courses, sections, enrollments)..."
cd /app && python -m brs_backend.seed_personas || true
echo "- Seeding users (authentication records)..."
cd /app && python -m brs_backend.seed_users || true

echo "Starting backend service..."
uvicorn brs_backend.main:app --host 0.0.0.0 --port 8000 --workers 1
