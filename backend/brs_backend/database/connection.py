"""Database configuration and session management for the BRS prototype."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from brs_backend.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Create a configured "Session" class
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """Provide a database session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
