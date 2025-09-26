"""Test API endpoints."""


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "openai_status" in data


class TestUserEndpoints:
    """Test user management endpoints."""

    def test_create_user(self, client, sample_user_data):
        """Test creating a new user."""
        response = client.post("/api/users/", json=sample_user_data)
        assert response.status_code == 201
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
        assert response.status_code == 201
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

    # Chat functionality is covered by dedicated integration tests for the
    # new SSE-based chat service. Those tests live alongside the chat module.
