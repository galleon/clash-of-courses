"""Test configuration and fixtures."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test.db"

# Ensure the application uses the test database before importing the app
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

from brs_backend.database.connection import get_db  # noqa: E402
from brs_backend.main import app  # noqa: E402
from brs_backend.models.database import Base  # noqa: E402

# Use in-memory SQLite for testing
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
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
