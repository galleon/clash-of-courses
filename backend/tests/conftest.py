"""Test configuration and fixtures."""

import os
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from brs_backend.database.connection import get_db  # noqa: E402
from brs_backend.main import app  # noqa: E402
from brs_backend.models.database import Base  # noqa: E402


@pytest.fixture(scope="session")
def test_database_url():
    """Create a temporary PostgreSQL test database for the test session."""
    test_db_name = f"test_brs_{str(uuid.uuid4()).replace('-', '_')}"

    # Connect to PostgreSQL to create the test database
    admin_engine = create_engine("postgresql://postgres:postgres@db:5432/postgres")

    try:
        # Create test database
        with admin_engine.connect() as conn:
            # Use autocommit to create database outside transaction
            conn.execute(text("COMMIT"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            print(f"✅ Created test database: {test_db_name}")

        # Return the test database URL
        test_db_url = f"postgresql://postgres:postgres@db:5432/{test_db_name}"

        # Set environment variable for the app
        os.environ["DATABASE_URL"] = test_db_url

        yield test_db_url

    finally:
        # Clean up: drop the test database
        try:
            with admin_engine.connect() as conn:
                # Terminate all connections to the test database
                conn.execute(text("COMMIT"))
                conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()
                """))
                # Drop the test database
                conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
                print(f"✅ Cleaned up test database: {test_db_name}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to clean up test database {test_db_name}: {e}")
        finally:
            admin_engine.dispose()


@pytest.fixture(scope="session")
def engine(test_database_url):
    """Create PostgreSQL engine for testing."""
    engine = create_engine(test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def TestingSessionLocal(engine):
    """Create session local class for testing."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db(engine):
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up tables after each test function
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(TestingSessionLocal, test_db):
    """Create test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()  # Rollback any pending transactions
        session.close()


def make_override_get_db(TestingSessionLocal):
    """Create override function for database dependency."""
    def override_get_db():
        """Override database dependency for testing."""
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    return override_get_db


@pytest.fixture(scope="function")
def client(test_db, TestingSessionLocal):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = make_override_get_db(TestingSessionLocal)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "test.student",
        "full_name": "Test Student",
        "role": "student",
        "email": "test.student@university.edu",
        "major": "Computer Science",
        "gpa": 3.5,
        "credit_hours_completed": 60,
        "age": 20,
        "gender": "Male",
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "code": "TEST101",
        "title": "Test Course",
        "description": "A test course",
        "credits": 3,
        "level": 100,
    }


@pytest.fixture
def sample_request_data():
    """Sample request data for testing."""
    return {
        "student_id": 1,
        "course_id": 1,
        "request_type": "add",
        "justification": "Need this course for my major",
    }
