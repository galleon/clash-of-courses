"""Test student tools functionality with PostgreSQL database."""

import uuid
from datetime import datetime, date
import pytest
from unittest.mock import patch
from brs_backend.models.database import (
    Campus, Course, Student, Program, Section, Term, Instructor,
    SectionMeeting, CampusRoom, Enrollment, RegistrationRequest
)
from brs_backend.agents.student_tools import (
    get_current_schedule, request_course_addition, check_attachable,
    create_automatic_enrollment, search_sections
)


class TestStudentTools:
    """Test student tools with PostgreSQL backend."""

    @pytest.fixture(autouse=True)
    def setup_database_mock(self, db_session):
        """Mock SessionLocal to use test database session."""
        with patch('brs_backend.agents.student_tools.SessionLocal') as mock_session_local:
            mock_session_local.return_value = db_session
            yield

    @pytest.fixture
    def sample_data(self, db_session):
        """Create sample data for testing."""
        # Create campus
        campus = Campus(name="Test Campus", location="Test Location")
        db_session.add(campus)
        db_session.flush()

        # Create program
        program = Program(
            name="Computer Science",
            max_credits=120,
            campus_id=campus.campus_id
        )
        db_session.add(program)
        db_session.flush()

        # Create student
        student = Student(
            external_sis_id="TEST001",
            gpa=3.5,
            credits_completed=60,
            standing="regular",
            student_status="following_plan",
            financial_status="clear",
            study_type="paid",
            program_id=program.program_id
        )
        db_session.add(student)
        db_session.flush()

        # Create courses
        course1 = Course(
            code="CS101",
            title="Introduction to Computer Science",
            credits=3,
            department_id=uuid.uuid4(),
            level=100,
            course_type="major",
            semester_pattern="both",
            delivery_mode="in_person",
            campus_id=campus.campus_id
        )
        course2 = Course(
            code="ENGR101",
            title="Introduction to Engineering",
            credits=3,
            department_id=uuid.uuid4(),
            level=100,
            course_type="major",
            semester_pattern="both",
            delivery_mode="in_person",
            campus_id=campus.campus_id
        )
        db_session.add_all([course1, course2])
        db_session.flush()

        # Create term
        term = Term(
            name="Fall 2024",
            starts_on=date(2024, 9, 1),
            ends_on=date(2024, 12, 15)
        )
        db_session.add(term)
        db_session.flush()

        # Create instructor
        instructor = Instructor(
            name="Prof. Test",
            department_id=uuid.uuid4(),
            campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()

        # Create room
        room = CampusRoom(name="Room 101", capacity=30, campus_id=campus.campus_id)
        db_session.add(room)
        db_session.flush()

        # Create sections
        section1 = Section(
            course_id=course1.course_id,
            term_id=term.term_id,
            section_code="S01",
            instructor_id=instructor.instructor_id,
            capacity=30,
            campus_id=campus.campus_id
        )
        section2 = Section(
            course_id=course1.course_id,
            term_id=term.term_id,
            section_code="S02",
            instructor_id=instructor.instructor_id,
            capacity=25,
            campus_id=campus.campus_id
        )
        section3 = Section(
            course_id=course2.course_id,
            term_id=term.term_id,
            section_code="S01",
            instructor_id=instructor.instructor_id,
            capacity=30,
            campus_id=campus.campus_id
        )
        db_session.add_all([section1, section2, section3])
        db_session.flush()

        # Create section meetings with PostgreSQL TSRANGE format
        meeting1 = SectionMeeting(
            section_id=section1.section_id,
            activity="LEC",
            day_of_week=1,  # Monday
            time_range="[2025-01-01 10:00:00,2025-01-01 11:30:00)",
            room_id=room.room_id
        )
        meeting2 = SectionMeeting(
            section_id=section2.section_id,
            activity="LEC",
            day_of_week=2,  # Tuesday
            time_range="[2025-01-01 13:00:00,2025-01-01 14:30:00)",
            room_id=room.room_id
        )
        meeting3 = SectionMeeting(
            section_id=section3.section_id,
            activity="LEC",
            day_of_week=1,  # Monday (conflicts with section1)
            time_range="[2025-01-01 10:00:00,2025-01-01 11:30:00)",
            room_id=room.room_id
        )
        db_session.add_all([meeting1, meeting2, meeting3])
        db_session.commit()

        return {
            "campus": campus,
            "program": program,
            "student": student,
            "courses": [course1, course2],
            "sections": [section1, section2, section3],
            "term": term,
            "instructor": instructor,
            "room": room
        }

    def test_get_current_schedule_empty(self, db_session, sample_data):
        """Test getting schedule for student with no enrollments."""
        student = sample_data["student"]
        
        result = get_current_schedule(str(student.student_id))
        
        assert result["success"] is True
        assert result["data"]["total_credits"] == 0
        assert result["data"]["course_count"] == 0
        assert len(result["data"]["schedule"]) == 0
        print("✅ Empty schedule test passed")

    def test_get_current_schedule_with_enrollment(self, db_session, sample_data):
        """Test getting schedule for student with enrollments."""
        student = sample_data["student"]
        section = sample_data["sections"][0]  # CS101 S01
        
        # Create enrollment
        enrollment = Enrollment(
            student_id=student.student_id,
            section_id=section.section_id,
            status="registered",
            enrolled_at=datetime.utcnow()
        )
        db_session.add(enrollment)
        db_session.commit()
        
        result = get_current_schedule(str(student.student_id))
        
        assert result["success"] is True
        assert result["data"]["total_credits"] == 3
        assert result["data"]["course_count"] == 1
        assert len(result["data"]["schedule"]) == 1
        assert result["data"]["schedule"][0]["course_code"] == "CS101"
        assert result["data"]["schedule"][0]["status"] == "enrolled"
        print("✅ Schedule with enrollment test passed")

    def test_search_sections(self, db_session, sample_data):
        """Test searching for course sections."""
        result = search_sections("CS101")
        
        assert result["success"] is True
        assert result["data"]["total_count"] == 1
        course_data = result["data"]["courses"][0]
        assert course_data["code"] == "CS101"
        assert len(course_data["sections"]) == 2  # S01 and S02
        print("✅ Search sections test passed")

    def test_check_attachable_no_conflicts(self, db_session, sample_data):
        """Test checking if student can attach to section with no conflicts."""
        student = sample_data["student"]
        section = sample_data["sections"][1]  # CS101 S02 (Tuesday, no conflicts)
        
        result = check_attachable(str(student.student_id), str(section.section_id))
        
        assert result["success"] is True
        assert result["attachable"] is True
        assert len(result["violations"]) == 0
        print("✅ Check attachable (no conflicts) test passed")

    def test_check_attachable_with_time_conflict(self, db_session, sample_data):
        """Test checking attachable with time conflicts."""
        student = sample_data["student"]
        section1 = sample_data["sections"][0]  # CS101 S01 (Monday)
        section3 = sample_data["sections"][2]  # ENGR101 S01 (Monday, conflicts)
        
        # First enroll in CS101 S01
        enrollment = Enrollment(
            student_id=student.student_id,
            section_id=section1.section_id,
            status="registered",
            enrolled_at=datetime.utcnow()
        )
        db_session.add(enrollment)
        db_session.commit()
        
        # Now check if can attach to ENGR101 S01 (should conflict)
        result = check_attachable(str(student.student_id), str(section3.section_id))
        
        assert result["success"] is True
        assert result["attachable"] is False
        assert len(result["violations"]) > 0
        assert any("Time conflict" in v["message"] for v in result["violations"])
        print("✅ Check attachable (with conflict) test passed")

    def test_create_automatic_enrollment(self, db_session, sample_data):
        """Test automatic enrollment creation."""
        student = sample_data["student"]
        section = sample_data["sections"][1]  # CS101 S02
        
        # Store IDs before calling the function to avoid session detachment issues
        student_id = student.student_id
        section_id = section.section_id
        
        result = create_automatic_enrollment(
            str(student_id),
            str(section_id),
            "Test enrollment"
        )
        
        assert result["success"] is True
        assert result["course_code"] == "CS101"
        assert result["section_code"] == "S02"
        assert "enrollment_id" in result
        
        # Verify enrollment was created in database
        enrollment = db_session.query(Enrollment).filter_by(
            student_id=student_id,
            section_id=section_id
        ).first()
        assert enrollment is not None
        assert enrollment.status == "registered"
        print("✅ Automatic enrollment test passed")

    def test_request_course_addition_success(self, db_session, sample_data):
        """Test successful course addition request."""
        student = sample_data["student"]
        
        result = request_course_addition(
            str(student.student_id),
            "CS101",
            "S02",
            "Test addition"
        )
        
        assert result["success"] is True
        assert result["data"]["auto_enrolled"] is True
        assert result["data"]["course_code"] == "CS101"
        
        # Verify the schedule was updated in the response
        assert "total_credits" in result["data"]
        assert "schedule" in result["data"]
        print("✅ Course addition (success) test passed")

    def test_request_course_addition_with_conflict_resolution(self, db_session, sample_data):
        """Test course addition with conflict resolution."""
        student = sample_data["student"]
        section1 = sample_data["sections"][0]  # CS101 S01 (Monday)
        
        # First enroll in CS101 S01
        enrollment = Enrollment(
            student_id=student.student_id,
            section_id=section1.section_id,
            status="registered",
            enrolled_at=datetime.utcnow()
        )
        db_session.add(enrollment)
        db_session.commit()
        
        # Now try to add ENGR101 S01 (should conflict and suggest alternatives)
        result = request_course_addition(
            str(student.student_id),
            "ENGR101",
            "S01",
            "Test conflicting addition"
        )
        
        # Should fail due to conflict but provide alternatives
        assert result["success"] is False
        assert "conflict" in result["error"].lower()
        print("✅ Course addition (with conflict) test passed")

    def test_postgresql_tsrange_parsing(self, db_session, sample_data):
        """Test that PostgreSQL TSRANGE values are properly parsed."""
        result = search_sections("CS101")
        
        assert result["success"] is True
        course_data = result["data"]["courses"][0]
        section = course_data["sections"][0]
        meeting = section["meetings"][0]
        
        # Verify time parsing from PostgreSQL TSRANGE
        assert meeting["start_time"] == "2025-01-01 10:00:00"
        assert meeting["end_time"] == "2025-01-01 11:30:00"
        assert meeting["day_of_week"] in [1, 2]  # Monday or Tuesday
        assert meeting["activity"] == "LEC"
        print("✅ PostgreSQL TSRANGE parsing test passed")

    def test_schedule_update_after_enrollment(self, db_session, sample_data):
        """Test that schedule updates correctly after enrollment (the fix we implemented)."""
        student = sample_data["student"]
        
        # Get initial schedule (should be empty)
        initial_schedule = get_current_schedule(str(student.student_id))
        assert initial_schedule["data"]["total_credits"] == 0
        
        # Add a course
        result = request_course_addition(
            str(student.student_id),
            "CS101",
            "S02",
            "Test enrollment with schedule update"
        )
        
        assert result["success"] is True
        assert result["data"]["auto_enrolled"] is True
        
        # The response should include updated schedule data
        assert result["data"]["total_credits"] == 3
        assert len(result["data"]["schedule"]) == 1
        assert result["data"]["schedule"][0]["course_code"] == "CS101"
        
        # Also verify by calling get_current_schedule directly
        updated_schedule = get_current_schedule(str(student.student_id))
        assert updated_schedule["data"]["total_credits"] == 3
        assert len(updated_schedule["data"]["schedule"]) == 1
        
        print("✅ Schedule update after enrollment test passed")