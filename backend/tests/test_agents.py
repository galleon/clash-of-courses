"""Test agent tools functionality."""

from unittest.mock import Mock, patch

from src.models.database import User, Course, Section, Request


class TestStudentTools:
    """Test student agent tools."""

    def test_get_student_info(self, client, sample_user_data):
        """Test get_student_info tool."""
        # Create student user first
        user_response = client.post("/api/users/", json=sample_user_data)
        user_id = user_response.json()["id"]

        # Import and test the tool directly
        from src.agents.student_tools import get_student_info

        with patch("src.agents.student_tools.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_user = Mock()
            mock_user.id = user_id
            mock_user.username = sample_user_data["username"]
            mock_user.full_name = sample_user_data["full_name"]
            mock_user.role = "student"
            mock_user.gpa = sample_user_data["gpa"]
            mock_user.credit_hours_completed = sample_user_data[
                "credit_hours_completed"
            ]
            mock_user.major = sample_user_data["major"]

            mock_db.query.return_value.filter_by.return_value.first.return_value = (
                mock_user
            )

            result = get_student_info(user_id)

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["data"]["username"] == sample_user_data["username"]
            assert result["data"]["gpa"] == sample_user_data["gpa"]

    def test_search_courses(self):
        """Test search_courses tool."""
        from src.agents.student_tools import search_courses

        with patch("src.agents.student_tools.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_course = Mock()
            mock_course.id = 1
            mock_course.code = "CS101"
            mock_course.name = "Introduction to Computer Science"
            mock_course.description = "Basic programming concepts"
            mock_course.credits = 3

            mock_db.query.return_value.filter.return_value.all.return_value = [
                mock_course
            ]

            result = search_courses("computer science")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert len(result["data"]) == 1
            assert result["data"][0]["code"] == "CS101"

    def test_create_registration_request(self):
        """Test create_registration_request tool."""
        from src.agents.student_tools import create_registration_request

        with patch("src.agents.student_tools.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            # Mock user and course existence
            mock_db.query.return_value.get.side_effect = [Mock(id=1), Mock(id=1)]

            result = create_registration_request(1, 1, "Need this course for my major")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert "request created" in result["message"].lower()


class TestAdvisorTools:
    """Test advisor agent tools."""

    def test_approve_request(self):
        """Test approve_request tool."""
        from src.agents.advisor_tools import approve_request

        with patch("src.agents.advisor_tools.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_request = Mock()
            mock_request.id = 1
            mock_request.status = "pending"
            mock_db.query.return_value.get.return_value = mock_request

            result = approve_request(1, 1, "Student meets requirements")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert "approved" in result["message"].lower()

    def test_get_advisor_info(self):
        """Test get_advisor_info tool."""
        from src.agents.advisor_tools import get_advisor_info

        with patch("src.agents.advisor_tools.SessionLocal") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db

            mock_advisor = Mock()
            mock_advisor.id = 1
            mock_advisor.username = "dr.smith"
            mock_advisor.full_name = "Dr. Smith"
            mock_advisor.role = "advisor"
            mock_advisor.major = "Computer Science"

            mock_db.query.return_value.filter_by.return_value.first.return_value = (
                mock_advisor
            )

            result = get_advisor_info(1)

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["data"]["role"] == "advisor"
