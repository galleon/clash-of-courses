"""Database configuration and session management for the BRS prototype.

This module defines a SQLAlchemy engine and session factory to connect
to a PostgreSQL database. Connection settings are read from environment
variables to allow for flexible configuration in different environments.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/brs_prototype_db",
)

# Create the SQLAlchemy engine. In production you might enable
# connection pooling or async support.
engine = create_engine(DATABASE_URL, echo=False)

# Create a configured "Session" class
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for declarative models
Base = declarative_base()