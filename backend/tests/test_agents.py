"""Tests for agent utility functions against the SQLite test database."""

from brs_backend.agents.advisor_tools import approve_request, get_request_details
from brs_backend.agents.student_tools import (
    create_registration_request,
    find_course_by_code,
    get_student_info,
)


class TestStudentTools:
    """Validate student-facing agent helpers."""

    def test_get_student_info(self, client, sample_user_data):
        """Returns student profile summary with no enrollments."""
        user_response = client.post("/api/users/", json=sample_user_data)
        print(f"Response status: {user_response.status_code}")
        print(f"Response body: {user_response.json()}")
        user_id = user_response.json()["id"]  # User model uses "id" field

        result = get_student_info(user_id)
        print(f"get_student_info result: {result}")

        assert result["success"] is True
        assert result["error"] is None
        payload = result["data"]
        assert payload["full_name"] == sample_user_data["full_name"]
        assert payload["role"] == sample_user_data["role"]
        assert payload["total_enrolled_courses"] == 0
        assert payload["total_pending_requests"] == 0

    def test_find_course_by_code(self, client, sample_course_data):
        """Find an existing course by code."""
        client.post("/api/courses/", json=sample_course_data)

        result = find_course_by_code(sample_course_data["code"])

        assert result["success"] is True
        course = result["data"]
        assert course["course_code"] == sample_course_data["code"]
        assert course["course_name"] == sample_course_data["title"]

    def test_create_registration_request(
        self, client, sample_user_data, sample_course_data
    ):
        """Create a new pending registration request."""
        user_response = client.post("/api/users/", json=sample_user_data)
        student_id = user_response.json()["id"]
        client.post("/api/courses/", json=sample_course_data)

        result = create_registration_request(
            student_id=student_id,
            course_code=sample_course_data["code"],
            justification="Need this course for my major",
        )

        assert result["success"] is True
        request_payload = result["data"]
        assert request_payload["status"] == "pending"
        assert request_payload["student_id"] == student_id
        assert request_payload["course_code"] == sample_course_data["code"]


class TestAdvisorTools:
    """Validate advisor-facing agent helpers."""

    def test_approve_request(
        self, client, sample_user_data, sample_course_data, sample_request_data
    ):
        """Approve a pending request and confirm metadata."""
        advisor_data = sample_user_data.copy()
        advisor_data.update({"username": "advisor.user", "role": "advisor"})
        advisor_response = client.post("/api/users/", json=advisor_data)
        advisor_id = advisor_response.json()["id"]

        student_response = client.post("/api/users/", json=sample_user_data)
        student_id = student_response.json()["id"]
        client.post("/api/courses/", json=sample_course_data)

        request_result = create_registration_request(
            student_id=student_id,
            course_code=sample_course_data["code"],
            justification=sample_request_data["justification"],
        )
        request_id = request_result["data"]["request_id"]

        result = approve_request(request_id, advisor_id, "Student meets requirements")

        assert result["success"] is True
        data = result["data"]
        assert data["status"] == "approved"
        assert data["request_id"] == request_id
        assert data["advisor_id"] == advisor_id

    def test_get_request_details(
        self, client, sample_user_data, sample_course_data, sample_request_data
    ):
        """Retrieve structured details for a pending request."""
        student_response = client.post("/api/users/", json=sample_user_data)
        student_id = student_response.json()["id"]
        client.post("/api/courses/", json=sample_course_data)

        request_result = create_registration_request(
            student_id=student_id,
            course_code=sample_course_data["code"],
            justification=sample_request_data["justification"],
        )
        request_id = request_result["data"]["request_id"]

        result = get_request_details(request_id)

        assert result["success"] is True
        payload = result["data"]
        assert payload["request"]["id"] == request_id
        assert payload["request"]["student_id"] == student_id
        assert payload["course"]["code"] == sample_course_data["code"]
