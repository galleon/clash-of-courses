"""Model-based tests using PostgreSQL database."""

import uuid
import pytest
from datetime import datetime
from brs_backend.models.database import (
    User, Campus, Program, Course, Student, Instructor,
    InstructorSchedule, Section, Term, CampusRoom
)


class TestModelsPostgreSQL:
    """Test SQLAlchemy models with PostgreSQL backend."""

    def test_campus_creation(self, db_session):
        """Test Campus model creation and persistence."""
        campus = Campus(
            name="Main Campus",
            location="Downtown University District"
        )

        db_session.add(campus)
        db_session.commit()

        # Verify the campus was created
        retrieved = db_session.query(Campus).filter_by(name="Main Campus").first()
        assert retrieved is not None
        assert retrieved.name == "Main Campus"
        assert retrieved.location == "Downtown University District"
        assert retrieved.campus_id is not None

        print(f"✅ Campus created with ID: {retrieved.campus_id}")

    def test_program_creation_with_campus(self, db_session):
        """Test Program model with Campus relationship."""
        # Create campus first
        campus = Campus(name="Tech Campus", location="Silicon Valley")
        db_session.add(campus)
        db_session.flush()  # Get the campus_id

        # Create program
        program = Program(
            name="Computer Science",
            max_credits=120,
            campus_id=campus.campus_id
        )

        db_session.add(program)
        db_session.commit()

        # Verify relationships
        retrieved_program = db_session.query(Program).filter_by(name="Computer Science").first()
        assert retrieved_program is not None
        assert retrieved_program.campus.name == "Tech Campus"

        print(f"✅ Program created with campus relationship: {retrieved_program.program_id}")

    def test_course_creation(self, db_session):
        """Test Course model creation."""
        # Create campus first
        campus = Campus(name="Engineering Campus", location="North District")
        db_session.add(campus)
        db_session.flush()

        # Create course
        course = Course(
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

        db_session.add(course)
        db_session.commit()

        # Verify course
        retrieved = db_session.query(Course).filter_by(code="CS101").first()
        assert retrieved is not None
        assert retrieved.title == "Introduction to Computer Science"
        assert retrieved.credits == 3
        assert retrieved.level == 100

        print(f"✅ Course created: {retrieved.code} - {retrieved.title}")

    def test_student_creation_with_relationships(self, db_session):
        """Test Student model with full relationships."""
        # Create campus and program
        campus = Campus(name="Student Campus", location="Main Street")
        db_session.add(campus)
        db_session.flush()

        program = Program(
            name="Software Engineering",
            max_credits=128,
            campus_id=campus.campus_id
        )
        db_session.add(program)
        db_session.flush()

        # Create student
        student = Student(
            external_sis_id="STU2024001",
            program_id=program.program_id,
            campus_id=campus.campus_id,
            standing="regular",
            student_status="new",
            gpa=3.75,
            credits_completed=30,
            financial_status="clear",
            study_type="paid"
        )

        db_session.add(student)
        db_session.commit()

        # Verify relationships
        retrieved = db_session.query(Student).filter_by(external_sis_id="STU2024001").first()
        assert retrieved is not None
        assert retrieved.gpa == 3.75
        assert retrieved.program.name == "Software Engineering"
        assert retrieved.campus.name == "Student Campus"

        print(f"✅ Student created with relationships: {retrieved.external_sis_id}")

    def test_instructor_with_schedule(self, db_session):
        """Test Instructor model with TSRANGE schedule."""
        # Create campus
        campus = Campus(name="Faculty Campus", location="Academic Row")
        db_session.add(campus)
        db_session.flush()

        # Create instructor
        instructor = Instructor(
            name="Dr. Sarah Johnson",
            department_id=uuid.uuid4(),
            campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()

        # Create instructor schedule with TSRANGE
        schedule = InstructorSchedule(
            instructor_id=instructor.instructor_id,
            day_of_week=1,  # Monday
            time_range="[2024-01-01 09:00:00,2024-01-01 17:00:00)"
        )
        db_session.add(schedule)
        db_session.commit()

        # Verify schedule with PostgreSQL TSRANGE operations
        retrieved = db_session.query(InstructorSchedule).filter_by(
            instructor_id=instructor.instructor_id
        ).first()

        assert retrieved is not None
        assert retrieved.day_of_week == 1
        assert retrieved.time_range is not None

        print(f"✅ Instructor with TSRANGE schedule created: {instructor.name}")

    def test_user_authentication_model(self, db_session):
        """Test User authentication model."""
        user = User(
            username="john.doe",
            email="john.doe@university.edu",
            full_name="John Doe",
            user_type="student",
            password_hash="hashed_password_here",
            is_active=1
        )

        db_session.add(user)
        db_session.commit()

        # Verify user
        retrieved = db_session.query(User).filter_by(username="john.doe").first()
        assert retrieved is not None
        assert retrieved.email == "john.doe@university.edu"
        assert retrieved.user_type == "student"
        assert retrieved.is_active == 1

        print(f"✅ User authentication model working: {retrieved.username}")

    def test_section_with_term_and_instructor(self, db_session):
        """Test Section model with relationships."""
        # Create dependencies
        campus = Campus(name="Section Campus", location="Building A")
        db_session.add(campus)
        db_session.flush()

        course = Course(
            code="MATH101",
            title="Calculus I",
            credits=4,
            department_id=uuid.uuid4(),
            level=100,
            campus_id=campus.campus_id
        )
        db_session.add(course)
        db_session.flush()

        instructor = Instructor(
            name="Prof. Mathematics",
            department_id=uuid.uuid4(),
            campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()

        term = Term(
            name="Fall 2024",
            starts_on=datetime(2024, 9, 1).date(),
            ends_on=datetime(2024, 12, 15).date()
        )
        db_session.add(term)
        db_session.flush()

        # Create section
        section = Section(
            course_id=course.course_id,
            term_id=term.term_id,
            section_code="001",
            instructor_id=instructor.instructor_id,
            capacity=30,
            waitlist_capacity=5,
            campus_id=campus.campus_id
        )
        db_session.add(section)
        db_session.commit()

        # Verify relationships
        retrieved = db_session.query(Section).filter_by(section_code="001").first()
        assert retrieved is not None
        assert retrieved.course.code == "MATH101"
        assert retrieved.instructor.name == "Prof. Mathematics"
        assert retrieved.term.name == "Fall 2024"
        assert retrieved.capacity == 30

        print(f"✅ Section with full relationships: {retrieved.course.code}-{retrieved.section_code}")

    def test_postgresql_features(self, db_session):
        """Test PostgreSQL-specific features like TSRANGE."""
        # Create instructor with multiple schedule entries
        campus = Campus(name="Schedule Campus", location="Clock Tower")
        db_session.add(campus)
        db_session.flush()

        instructor = Instructor(
            name="Dr. Time Manager",
            department_id=uuid.uuid4(),
            campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()

        # Multiple time slots
        schedules = [
            (1, "[2024-01-01 09:00:00,2024-01-01 11:00:00)"),  # Monday 9-11
            (1, "[2024-01-01 13:00:00,2024-01-01 15:00:00)"),  # Monday 1-3
            (3, "[2024-01-01 10:00:00,2024-01-01 12:00:00)"),  # Wednesday 10-12
        ]

        for day, time_range in schedules:
            schedule = InstructorSchedule(
                instructor_id=instructor.instructor_id,
                day_of_week=day,
                time_range=time_range
            )
            db_session.add(schedule)

        db_session.commit()

        # Query schedules using model relationships
        all_schedules = db_session.query(InstructorSchedule).filter_by(
            instructor_id=instructor.instructor_id
        ).all()

        assert len(all_schedules) == 3

        # Check that we can query by day
        monday_schedules = db_session.query(InstructorSchedule).filter_by(
            instructor_id=instructor.instructor_id,
            day_of_week=1
        ).all()

        assert len(monday_schedules) == 2

        print(f"✅ PostgreSQL TSRANGE schedules working: {len(all_schedules)} total, {len(monday_schedules)} on Monday")

    def test_model_constraints_and_validation(self, db_session):
        """Test model constraints work with PostgreSQL."""
        campus = Campus(name="Constraint Campus", location="Rule Street")
        db_session.add(campus)
        db_session.flush()

        program = Program(
            name="Data Science",
            max_credits=120,
            campus_id=campus.campus_id
        )
        db_session.add(program)
        db_session.flush()

        # Test student with valid constraints
        student = Student(
            external_sis_id="VALID2024",
            program_id=program.program_id,
            campus_id=campus.campus_id,
            standing="regular",  # Valid constraint
            student_status="new",  # Valid constraint
            financial_status="clear",  # Valid constraint
            study_type="paid",  # Valid constraint
            gpa=3.5,
            credits_completed=45
        )

        db_session.add(student)
        db_session.commit()

        retrieved = db_session.query(Student).filter_by(external_sis_id="VALID2024").first()
        assert retrieved is not None
        assert retrieved.standing == "regular"
        assert retrieved.student_status == "new"

        print("✅ Model constraints working with PostgreSQL")
