"""SQLAlchemy models for the BRS database schema - Updated V3."""

import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    DECIMAL,
    ForeignKey,
    Text,
    TIMESTAMP,
    Date,
    CheckConstraint,
    UniqueConstraint,
    BIGINT,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, TSRANGE, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from brs_backend.database.connection import Base


# ===========================
# V3 UPDATED MODELS
# ===========================


class Campus(Base):
    __tablename__ = "campus"

    campus_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    location = Column(Text)

    # Relationships
    programs = relationship("Program", back_populates="campus")
    students = relationship("Student", back_populates="campus")
    courses = relationship("Course", back_populates="campus")
    rooms = relationship("CampusRoom", back_populates="campus")
    instructors = relationship("Instructor", back_populates="campus")
    sections = relationship("Section", back_populates="campus")


class Program(Base):
    __tablename__ = "program"

    program_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    max_credits = Column(Integer, nullable=False)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))

    # Relationships
    campus = relationship("Campus", back_populates="programs")
    students = relationship("Student", back_populates="program")


class Term(Base):
    __tablename__ = "term"

    term_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text)
    starts_on = Column(Date)
    ends_on = Column(Date)
    registration_starts_on = Column(Date)
    registration_ends_on = Column(Date)

    # Relationships
    sections = relationship("Section", back_populates="term")
    expected_graduate_students = relationship(
        "Student",
        foreign_keys="Student.expected_grad_term",
        back_populates="expected_grad_term_ref",
    )


class Student(Base):
    __tablename__ = "student"

    student_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_sis_id = Column(Text, unique=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("program.program_id"))
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))
    standing = Column(Text, nullable=False, default="regular")
    student_status = Column(Text)
    gpa = Column(DECIMAL(3, 2))
    credits_completed = Column(Integer, nullable=False, default=0)
    financial_status = Column(Text)
    study_type = Column(Text)
    expected_grad_term = Column(UUID(as_uuid=True), ForeignKey("term.term_id"))

    __table_args__ = (
        CheckConstraint(standing.in_(["regular", "probation", "suspended"])),
        CheckConstraint(
            student_status.in_(
                ["new", "following_plan", "expected_graduate", "struggling"]
            )
        ),
        CheckConstraint(financial_status.in_(["clear", "owed", "exempt"])),
        CheckConstraint(study_type.in_(["paid", "free", "scholarship"])),
    )

    # Relationships
    program = relationship("Program", back_populates="students")
    campus = relationship("Campus", back_populates="students")
    expected_grad_term_ref = relationship(
        "Term",
        foreign_keys=[expected_grad_term],
        back_populates="expected_graduate_students",
    )
    enrollments = relationship("Enrollment", back_populates="student")
    registration_requests = relationship(
        "RegistrationRequest", back_populates="student"
    )
    calendar_events = relationship("CalendarEvent", back_populates="student")
    preferences = relationship("StudentPreference", back_populates="student")
    signals = relationship("StudentSignal", back_populates="student")
    recommendations = relationship("Recommendation", back_populates="student")
    recommendation_feedback = relationship(
        "RecommendationFeedback", back_populates="student"
    )


class Course(Base):
    __tablename__ = "course"

    course_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    credits = Column(Integer, nullable=False)
    department_id = Column(UUID(as_uuid=True), nullable=False)
    level = Column(Integer, nullable=False)
    course_type = Column(Text)
    semester_pattern = Column(Text)
    delivery_mode = Column(Text)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))

    __table_args__ = (
        CheckConstraint(course_type.in_(["major", "university", "elective"])),
        CheckConstraint(semester_pattern.in_(["odd", "even", "both"])),
        CheckConstraint(delivery_mode.in_(["in_person", "online", "hybrid"])),
    )

    # Relationships
    campus = relationship("Campus", back_populates="courses")
    sections = relationship("Section", back_populates="course")
    prerequisite_requirements = relationship(
        "CoursePrereq", foreign_keys="CoursePrereq.course_id", back_populates="course"
    )
    required_by = relationship(
        "CoursePrereq",
        foreign_keys="CoursePrereq.req_course_id",
        back_populates="req_course",
    )


class CoursePrereq(Base):
    __tablename__ = "course_prereq"

    course_id = Column(
        UUID(as_uuid=True), ForeignKey("course.course_id"), primary_key=True
    )
    req_course_id = Column(
        UUID(as_uuid=True), ForeignKey("course.course_id"), primary_key=True
    )
    type = Column(Text, nullable=False, primary_key=True)

    __table_args__ = (CheckConstraint(type.in_(["prereq", "coreq", "equivalency"])),)

    # Relationships
    course = relationship(
        "Course", foreign_keys=[course_id], back_populates="prerequisite_requirements"
    )
    req_course = relationship(
        "Course", foreign_keys=[req_course_id], back_populates="required_by"
    )


class CampusRoom(Base):
    __tablename__ = "campus_room"

    room_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))
    name = Column(Text, nullable=False)
    capacity = Column(Integer, nullable=False)

    # Relationships
    campus = relationship("Campus", back_populates="rooms")
    meetings = relationship("SectionMeeting", back_populates="room")


class Instructor(Base):
    __tablename__ = "instructor"

    instructor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    department_id = Column(UUID(as_uuid=True), nullable=False)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))

    # Relationships
    campus = relationship("Campus", back_populates="instructors")
    schedules = relationship("InstructorSchedule", back_populates="instructor")
    sections = relationship("Section", back_populates="instructor")


class InstructorSchedule(Base):
    __tablename__ = "instructor_schedule"

    instructor_id = Column(
        UUID(as_uuid=True), ForeignKey("instructor.instructor_id"), primary_key=True
    )
    day_of_week = Column(Integer, nullable=False, primary_key=True)
    time_range = Column(TSRANGE, nullable=False, primary_key=True)

    __table_args__ = (CheckConstraint("day_of_week BETWEEN 0 AND 6"),)

    # Relationships
    instructor = relationship("Instructor", back_populates="schedules")


class Section(Base):
    __tablename__ = "section"

    section_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("course.course_id"))
    term_id = Column(UUID(as_uuid=True), ForeignKey("term.term_id"))
    section_code = Column(Text)
    instructor_id = Column(UUID(as_uuid=True), ForeignKey("instructor.instructor_id"))
    capacity = Column(Integer, nullable=False)
    waitlist_capacity = Column(Integer, default=0)
    campus_id = Column(UUID(as_uuid=True), ForeignKey("campus.campus_id"))

    __table_args__ = (UniqueConstraint("course_id", "term_id", "section_code"),)

    # Relationships
    course = relationship("Course", back_populates="sections")
    term = relationship("Term", back_populates="sections")
    instructor = relationship("Instructor", back_populates="sections")
    campus = relationship("Campus", back_populates="sections")
    meetings = relationship("SectionMeeting", back_populates="section")
    enrollments = relationship("Enrollment", back_populates="section")
    from_registration_requests = relationship(
        "RegistrationRequest",
        foreign_keys="RegistrationRequest.from_section_id",
        back_populates="from_section",
    )
    to_registration_requests = relationship(
        "RegistrationRequest",
        foreign_keys="RegistrationRequest.to_section_id",
        back_populates="to_section",
    )
    calendar_bindings = relationship("CalendarBinding", back_populates="section")


class SectionMeeting(Base):
    __tablename__ = "section_meeting"

    meeting_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("section.section_id", ondelete="CASCADE")
    )
    activity = Column(Text, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    time_range = Column(TSRANGE, nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("campus_room.room_id"))

    __table_args__ = (
        CheckConstraint(activity.in_(["LEC", "LAB", "TUT"])),
        CheckConstraint("day_of_week BETWEEN 0 AND 6"),
        Index("section_meeting_section_id_idx", "section_id"),
        Index(
            "section_meeting_tr_gist",
            "day_of_week",
            "time_range",
            postgresql_using="gist",
        ),
    )

    # Relationships
    section = relationship("Section", back_populates="meetings")
    room = relationship("CampusRoom", back_populates="meetings")
    calendar_bindings = relationship("CalendarBinding", back_populates="meeting")


class Enrollment(Base):
    __tablename__ = "enrollment"

    enrollment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.student_id"))
    section_id = Column(UUID(as_uuid=True), ForeignKey("section.section_id"))
    status = Column(Text, nullable=False)
    enrolled_at = Column(TIMESTAMP, default=func.now())

    __table_args__ = (
        CheckConstraint(status.in_(["registered", "waitlisted", "dropped"])),
        UniqueConstraint("student_id", "section_id"),
    )

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    section = relationship("Section", back_populates="enrollments")


class RegistrationRequest(Base):
    __tablename__ = "registration_request"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.student_id"))
    type = Column(Text, nullable=False)
    from_section_id = Column(UUID(as_uuid=True), ForeignKey("section.section_id"))
    to_section_id = Column(UUID(as_uuid=True), ForeignKey("section.section_id"))
    reason = Column(Text)
    state = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    __table_args__ = (
        CheckConstraint(type.in_(["ADD", "DROP", "CHANGE_SECTION"])),
        CheckConstraint(
            state.in_(
                [
                    "submitted",
                    "advisor_review",
                    "dept_review",
                    "approved",
                    "rejected",
                    "cancelled",
                ]
            )
        ),
    )

    # Relationships
    student = relationship("Student", back_populates="registration_requests")
    from_section = relationship(
        "Section",
        foreign_keys=[from_section_id],
        back_populates="from_registration_requests",
    )
    to_section = relationship(
        "Section",
        foreign_keys=[to_section_id],
        back_populates="to_registration_requests",
    )
    decisions = relationship("RequestDecision", back_populates="request")
    conflicts = relationship("RequestConflict", back_populates="request")


class RequestDecision(Base):
    __tablename__ = "request_decision"

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registration_request.request_id", ondelete="CASCADE"),
    )
    actor_role = Column(Text)
    action = Column(Text)
    rationale = Column(Text)
    decided_at = Column(TIMESTAMP, default=func.now())

    __table_args__ = (
        CheckConstraint(actor_role.in_(["advisor", "department_head"])),
        CheckConstraint(action.in_(["approve", "reject", "refer", "hold"])),
    )

    # Relationships
    request = relationship("RegistrationRequest", back_populates="decisions")


class RequestConflict(Base):
    __tablename__ = "request_conflict"

    id = Column(BIGINT, primary_key=True, autoincrement=True)  # BIGSERIAL
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("registration_request.request_id", ondelete="CASCADE"),
    )
    rule_code = Column(Text)
    details = Column(JSONB)

    # Relationships
    request = relationship("RegistrationRequest", back_populates="conflicts")


class CalendarEvent(Base):
    __tablename__ = "calendar_event"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.student_id"))
    source = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    starts_at = Column(TIMESTAMP, nullable=False)
    ends_at = Column(TIMESTAMP, nullable=False)
    location = Column(Text)
    payload = Column(JSONB)

    __table_args__ = (CheckConstraint(source.in_(["system", "external"])),)

    # Relationships
    student = relationship("Student", back_populates="calendar_events")
    bindings = relationship("CalendarBinding", back_populates="event")


class CalendarBinding(Base):
    __tablename__ = "calendar_binding"

    binding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(
        UUID(as_uuid=True), ForeignKey("calendar_event.event_id", ondelete="CASCADE")
    )
    section_id = Column(UUID(as_uuid=True), ForeignKey("section.section_id"))
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("section_meeting.meeting_id"))

    __table_args__ = (UniqueConstraint("event_id", "section_id", "meeting_id"),)

    # Relationships
    event = relationship("CalendarEvent", back_populates="bindings")
    section = relationship("Section", back_populates="calendar_bindings")
    meeting = relationship("SectionMeeting", back_populates="calendar_bindings")


class StudentPreference(Base):
    __tablename__ = "student_preference"

    student_id = Column(
        UUID(as_uuid=True), ForeignKey("student.student_id"), primary_key=True
    )
    key = Column(Text, primary_key=True)
    value = Column(JSONB)

    # Relationships
    student = relationship("Student", back_populates="preferences")


class StudentSignal(Base):
    __tablename__ = "student_signal"

    id = Column(BIGINT, primary_key=True, autoincrement=True)  # BIGSERIAL
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.student_id"))
    signal_type = Column(Text)
    signal_value = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    student = relationship("Student", back_populates="signals")


class Recommendation(Base):
    __tablename__ = "recommendation"

    rec_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student.student_id"))
    kind = Column(Text)
    proposal = Column(JSONB)
    features = Column(JSONB)
    score = Column(DECIMAL)  # DOUBLE PRECISION
    created_at = Column(TIMESTAMP, default=func.now())

    __table_args__ = (
        CheckConstraint(kind.in_(["add_course", "swap_section", "cancel_course"])),
    )

    # Relationships
    student = relationship("Student", back_populates="recommendations")
    feedback = relationship("RecommendationFeedback", back_populates="recommendation")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    rec_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recommendation.rec_id", ondelete="CASCADE"),
        primary_key=True,
    )
    student_id = Column(
        UUID(as_uuid=True), ForeignKey("student.student_id"), primary_key=True
    )
    feedback = Column(Text)

    __table_args__ = (
        CheckConstraint(
            feedback.in_(["accept", "reject", "later", "thumbs_up", "thumbs_down"])
        ),
    )

    # Relationships
    recommendation = relationship("Recommendation", back_populates="feedback")
    student = relationship("Student", back_populates="recommendation_feedback")


# Keep the original User model for backward compatibility with authentication
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(
        String(30), nullable=False
    )  # student, advisor, department_head, registrar
    email = Column(String, unique=True)

    # Additional fields for compatibility
    age = Column(Integer)
    gender = Column(String(10))
    major = Column(String(100))
    gpa = Column(DECIMAL(3, 2))
    credit_hours_completed = Column(Integer, nullable=False, default=0)
    technology_proficiency = Column(String(50))
    description = Column(Text)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
