"""Test API endpoints."""

import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "database" in data
        assert "agents" in data


class TestUserEndpoints:
    """Test user management endpoints."""

    def test_create_user(self, client, sample_user_data):
        """Test creating a new user."""
        response = client.post("/api/users/", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user_data["username"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert data["role"] == sample_user_data["role"]
        assert "id" in data

    def test_get_user(self, client, sample_user_data):
        """Test retrieving a user."""
        # Create user first
        create_response = client.post("/api/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Get user
        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == sample_user_data["username"]

    def test_get_user_not_found(self, client):
        """Test retrieving non-existent user."""
        response = client.get("/api/users/999")
        assert response.status_code == 404

    def test_list_users(self, client, sample_user_data):
        """Test listing all users."""
        # Create a user first
        client.post("/api/users/", json=sample_user_data)

        response = client.get("/api/users/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_update_user(self, client, sample_user_data):
        """Test updating a user."""
        # Create user first
        create_response = client.post("/api/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Update user
        updated_data = sample_user_data.copy()
        updated_data["gpa"] = 3.8
        response = client.put(f"/api/users/{user_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["gpa"] == 3.8

    def test_delete_user(self, client, sample_user_data):
        """Test deleting a user."""
        # Create user first
        create_response = client.post("/api/users/", json=sample_user_data)
        user_id = create_response.json()["id"]

        # Delete user
        response = client.delete(f"/api/users/{user_id}")
        assert response.status_code == 200

        # Verify user is deleted
        get_response = client.get(f"/api/users/{user_id}")
        assert get_response.status_code == 404


class TestRequestEndpoints:
    """Test request management endpoints."""

    def test_create_request(
        self, client, sample_user_data, sample_course_data, sample_request_data
    ):
        """Test creating a new registration request."""
        # Create user and course first
        user_response = client.post("/api/users/", json=sample_user_data)
        user_id = user_response.json()["id"]

        course_response = client.post("/api/courses/", json=sample_course_data)
        course_id = course_response.json()["id"]

        # Create request
        request_data = sample_request_data.copy()
        request_data["student_id"] = user_id
        request_data["course_id"] = course_id

        response = client.post("/api/requests/", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == user_id
        assert data["course_id"] == course_id
        assert data["status"] == "pending"
        assert "id" in data

    def test_list_requests(
        self, client, sample_user_data, sample_course_data, sample_request_data
    ):
        """Test listing all requests."""
        # Create user, course, and request first
        user_response = client.post("/api/users/", json=sample_user_data)
        user_id = user_response.json()["id"]

        course_response = client.post("/api/courses/", json=sample_course_data)
        course_id = course_response.json()["id"]

        request_data = sample_request_data.copy()
        request_data["student_id"] = user_id
        request_data["course_id"] = course_id
        client.post("/api/requests/", json=request_data)

        response = client.get("/api/requests/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_approve_request(
        self, client, sample_user_data, sample_course_data, sample_request_data
    ):
        """Test approving a request."""
        # Create advisor user
        advisor_data = sample_user_data.copy()
        advisor_data["username"] = "test.advisor"
        advisor_data["role"] = "advisor"
        advisor_response = client.post("/api/users/", json=advisor_data)
        advisor_id = advisor_response.json()["id"]

        # Create student user and course
        user_response = client.post("/api/users/", json=sample_user_data)
        user_id = user_response.json()["id"]

        course_response = client.post("/api/courses/", json=sample_course_data)
        course_id = course_response.json()["id"]

        # Create request
        request_data = sample_request_data.copy()
        request_data["student_id"] = user_id
        request_data["course_id"] = course_id
        request_response = client.post("/api/requests/", json=request_data)
        request_id = request_response.json()["id"]

        # Approve request
        decision_data = {
            "decision": "approved",
            "rationale": "Student meets all requirements",
        }
        response = client.post(
            f"/api/requests/{request_id}/approve/{advisor_id}", json=decision_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "approved" in data["message"].lower()


class TestChatEndpoints:
    """Test chat endpoints."""

    def test_student_chat(self, client, sample_user_data):
        """Test student chat endpoint."""
        # Create student user first
        user_response = client.post("/api/users/", json=sample_user_data)
        user_id = user_response.json()["id"]

        chat_data = {
            "message": "Hello, I need help with course registration",
            "student_id": user_id,
        }

        response = client.post("/api/chat/student", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)

    def test_advisor_chat(self, client, sample_user_data):
        """Test advisor chat endpoint."""
        # Create advisor user first
        advisor_data = sample_user_data.copy()
        advisor_data["username"] = "test.advisor"
        advisor_data["role"] = "advisor"
        user_response = client.post("/api/users/", json=advisor_data)
        advisor_id = user_response.json()["id"]

        chat_data = {
            "message": "Show me pending registration requests",
            "advisor_id": advisor_id,
        }

        response = client.post("/api/chat/advisor", json=chat_data)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
