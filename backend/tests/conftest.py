"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.connection import get_db
from src.main import app
from src.models.database import Base

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"
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
        "age": 20,
        "gender": "Male",
        "major": "Computer Science",
        "gpa": 3.5,
        "credit_hours_completed": 60,
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "code": "TEST101",
        "name": "Test Course",
        "description": "A test course",
        "credits": 3,
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
