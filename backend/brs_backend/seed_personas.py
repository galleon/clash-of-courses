"""
Seed script for the Student Course Management system.

This script does not connect to a live database.  Instead it assembles
a coherent set of in‑memory records that mirror the schema described in
the project.  The intention is to make it easy to test agents and
approval flows without having to populate a real database.  Each table
from the schema is represented as a list of dictionaries with keys
matching the column names.  UUIDs are generated on the fly so the
records look realistic.  Timestamps and dates are chosen to fall
within the 2025‑26 academic year.

Two sample scenarios are covered:

* Sarah Ahmed is a second‑year engineering student.  She is already
  enrolled in a section that meets on Monday morning.  When she
  attempts to register for another section that overlaps with her
  existing class the system should detect the time conflict.

* Mohammed Hassan and Fatima Al‑Zahra are included to provide
  additional personas for testing approval and eligibility rules.  They
  are assigned different standing, GPA and credit counts to exercise
  the BR‑001 (academic standing) and BR‑003 (credit limit) rules from
  the PRD.

To use this module in your tests simply import the ``get_seed_data``
function and call it.  It returns a dictionary keyed by table name.

Example::

    from seed_personas import get_seed_data
    data = get_seed_data()
    students = data['student']
    print(students[0])

You can also run this script directly to see a summary of the seeded
records.
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone


def _uuid() -> str:
    """Generate a stringified UUID."""
    return str(uuid.uuid4())


def _tsrange(start: time, end: time) -> str:
    """Represent a time range in PostgreSQL tsrange notation.

    The ``section_meeting`` table uses the ``TSRANGE`` type with
    half‑open intervals.  This helper function produces a string of the
    form ``[HH:MM,HH:MM)`` which can later be cast to ``TSRANGE`` by
    the database layer.
    """
    return f"[{start.strftime('%H:%M')},{end.strftime('%H:%M')})"


def get_seed_data() -> dict:
    """Assemble seed data for all core tables, including our proposed
    extensions.

    The returned structure contains rows for the new ``campus`` and
    ``program`` tables as well as additional columns on existing tables
    (financial_status, study_type, student_status, expected_grad_term,
    course_type, semester_pattern, delivery_mode and campus_id).  It also
    includes a sample room and instructor to illustrate how the
    extended schema can be populated.

    Returns:
        dict: A mapping from table name to a list of row dictionaries.
    """
    now = datetime.now(tz=timezone.utc)

    # ------------------------------------------------------------------
    # Campuses
    # We create a single campus for testing.  Additional campuses can
    # easily be added by duplicating this record with new UUIDs.
    campus_main_id = _uuid()
    campuses = [
        {
            "campus_id": campus_main_id,
            "name": "Main Campus",
            "location": "Downtown",
        },
    ]

    # ------------------------------------------------------------------
    # Programs
    # Create a single engineering program with a credit limit of 18
    # hours per term.  The ``campus_id`` ties the program to the
    # ``Main Campus`` record above.
    program_engineering_id = _uuid()
    programs = [
        {
            "program_id": program_engineering_id,
            "name": "Bachelor of Engineering",
            "max_credits": 18,
            "campus_id": campus_main_id,
        },
    ]

    # ------------------------------------------------------------------
    # Terms
    # A single term (2025‑Fall) covering September through December.  We
    # also define a registration window from mid‑June to mid‑August.
    term_fall_2025_id = _uuid()
    terms = [
        {
            "term_id": term_fall_2025_id,
            "name": "2025-Fall",
            "starts_on": date(2025, 9, 1),
            "ends_on": date(2025, 12, 20),
            "registration_starts_on": date(2025, 6, 15),
            "registration_ends_on": date(2025, 8, 15),
        },
    ]

    # ------------------------------------------------------------------
    # Students
    # Each student record includes the new fields: financial_status,
    # study_type, student_status, expected_grad_term and campus_id.  All
    # three students are associated with the engineering program and the
    # main campus.  Sarah is expected to graduate in 2027; Mohammed in
    # 2025; and Fatima in 2028.
    student_sarah_id = _uuid()
    student_mohammed_id = _uuid()
    student_fatima_id = _uuid()
    students = [
        {
            "student_id": student_sarah_id,
            "external_sis_id": "S1001",
            "program_id": program_engineering_id,
            "campus_id": campus_main_id,
            "standing": "regular",
            "student_status": "following_plan",
            "gpa": 3.2,
            "credits_completed": 45,
            "financial_status": "clear",
            "study_type": "paid",
            "expected_grad_term": None,  # left NULL in the DB
        },
        {
            "student_id": student_mohammed_id,
            "external_sis_id": "S1002",
            "program_id": program_engineering_id,
            "campus_id": campus_main_id,
            "standing": "regular",
            "student_status": "expected_graduate",
            "gpa": 2.8,
            "credits_completed": 110,
            "financial_status": "clear",
            "study_type": "paid",
            "expected_grad_term": term_fall_2025_id,
        },
        {
            "student_id": student_fatima_id,
            "external_sis_id": "S1003",
            "program_id": program_engineering_id,
            "campus_id": campus_main_id,
            "standing": "regular",
            "student_status": "new",
            "gpa": 3.8,
            "credits_completed": 15,
            "financial_status": "exempt",
            "study_type": "scholarship",
            "expected_grad_term": None,
        },
    ]

    # ------------------------------------------------------------------
    # Courses
    # Two sample courses with additional descriptive fields.  Both
    # courses are offered at the Main Campus and delivered in person.
    course_a_id = _uuid()
    course_b_id = _uuid()
    courses = [
        {
            "course_id": course_a_id,
            "code": "ENGR101",
            "title": "Introduction to Engineering",
            "credits": 3,
            "department_id": _uuid(),
            "level": 100,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
        {
            "course_id": course_b_id,
            "code": "ENGR201",
            "title": "Engineering Mechanics",
            "credits": 3,
            "department_id": _uuid(),
            "level": 200,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
    ]
    # ------------------------------------------------------------------
    # Course prerequisites
    # ENGR201 has ENGR101 as a prerequisite.
    course_prereqs = [
        {
            "course_id": course_b_id,
            "req_course_id": course_a_id,
            "type": "prereq",
        },
    ]

    # ------------------------------------------------------------------
    # Campuses rooms
    # Create a single classroom on the main campus.  In a real system
    # multiple rooms with varying capacities would be defined.
    room_main_id = _uuid()
    campus_rooms = [
        {
            "room_id": room_main_id,
            "campus_id": campus_main_id,
            "name": "ENGR-101",
            "capacity": 40,
        },
    ]

    # ------------------------------------------------------------------
    # Instructors
    # Two instructors are provided.  Their schedules are kept empty
    # here; the agent can populate ``instructor_schedule`` as needed.
    instructor_ahmad_id = _uuid()
    instructor_layla_id = _uuid()
    instructors = [
        {
            "instructor_id": instructor_ahmad_id,
            "name": "Dr. Ahmad Mahmoud",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
        {
            "instructor_id": instructor_layla_id,
            "name": "Dr. Layla Khalil",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
    ]

    instructor_schedule: list = []

    # ------------------------------------------------------------------
    # Sections and meetings
    # Course A has two sections at different times.  Course B has one
    # section that overlaps with Sarah's existing class.  By enrolling
    # Sarah in Section A1 and then attempting to add Section B1, a
    # schedule conflict is created.  Each section references the campus
    # and an instructor.
    section_a1_id = _uuid()
    section_a2_id = _uuid()
    section_b1_id = _uuid()
    sections = [
        {
            "section_id": section_a1_id,
            "course_id": course_a_id,
            "term_id": term_fall_2025_id,
            "section_code": "A1",
            "instructor_id": instructor_ahmad_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_a2_id,
            "course_id": course_a_id,
            "term_id": term_fall_2025_id,
            "section_code": "A2",
            "instructor_id": instructor_layla_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_b1_id,
            "course_id": course_b_id,
            "term_id": term_fall_2025_id,
            "section_code": "B1",
            "instructor_id": instructor_ahmad_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
    ]

    # Each section has one meeting block for simplicity.  The conflict
    # occurs on Monday when ENGR101 A1 runs from 10:00–11:15 and
    # ENGR201 B1 runs from 10:30–11:45.  Meetings reference the
    # ``room_id`` rather than a string name.
    section_meetings = [
        {
            "meeting_id": _uuid(),
            "section_id": section_a1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday
            "time_range": _tsrange(time(10, 0), time(11, 15)),
            "room_id": room_main_id,
        },
        {
            "meeting_id": _uuid(),
            "section_id": section_a2_id,
            "activity": "LEC",
            "day_of_week": 2,  # Wednesday
            "time_range": _tsrange(time(14, 0), time(15, 15)),
            "room_id": room_main_id,
        },
        {
            "meeting_id": _uuid(),
            "section_id": section_b1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday
            "time_range": _tsrange(time(10, 30), time(11, 45)),
            "room_id": room_main_id,
        },
    ]
    # ------------------------------------------------------------------
    # Initial enrollments
    # Sarah is already registered in ENGR101 A1.  Mohammed and
    # Fatima are not yet enrolled in any sections.  Enrollment status is
    # set to "registered" for active registrations.
    enrollment = [
        {
            "enrollment_id": _uuid(),
            "student_id": student_sarah_id,
            "section_id": section_a1_id,
            "status": "registered",
            "enrolled_at": now,
        },
    ]

    # ------------------------------------------------------------------
    # Registration requests
    # We do not pre‑populate any registration requests here.  During
    # testing the agent can create a request for Sarah to add ENGR201
    # B1 and observe the resulting conflict.
    registration_requests: list = []
    request_decisions: list = []
    request_conflicts: list = []

    # ------------------------------------------------------------------
    # Preferences and signals – left empty for now
    student_preference: list = []
    student_signal: list = []

    # ------------------------------------------------------------------
    # Recommendations – left empty for now
    recommendation: list = []
    recommendation_feedback: list = []

    return {
        "campus": campuses,
        "program": programs,
        "term": terms,
        "student": students,
        "course": courses,
        "course_prereq": course_prereqs,
        "campus_room": campus_rooms,
        "instructor": instructors,
        "instructor_schedule": instructor_schedule,
        "section": sections,
        "section_meeting": section_meetings,
        "enrollment": enrollment,
        "registration_request": registration_requests,
        "request_decision": request_decisions,
        "request_conflict": request_conflicts,
        "student_preference": student_preference,
        "student_signal": student_signal,
        "recommendation": recommendation,
        "recommendation_feedback": recommendation_feedback,
    }


def _pretty_print(data: dict) -> None:
    """Pretty print a summary of the seeded data for debugging.

    Args:
        data (dict): The dictionary returned by ``get_seed_data``.
    """
    for table, rows in data.items():
        print(f"Table {table}: {len(rows)} rows")
        for row in rows:
            print(f"  {row}")
        print()


if __name__ == "__main__":  # pragma: no cover
    seed = get_seed_data()
    _pretty_print(seed)
