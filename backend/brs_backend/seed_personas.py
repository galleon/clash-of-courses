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
    # Display first student for verification
    logger.info(f"First student: {students[0]}")

You can also run this script directly to see a summary of the seeded
records.
"""

import uuid
from uuid import UUID
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



import uuid
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


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
    # students are associated with the engineering program and the
    # main campus. We include additional students to create realistic
    # enrollment numbers for testing.
    # Sarah Ahmed (our main test student) - Use fixed UUID for consistent testing
    student_sarah_id = UUID("4441ab90-e2fe-4da5-a0e1-6a129d61552f")
    student_mohammed_id = _uuid()
    student_fatima_id = _uuid()

    # Additional students for realistic enrollment counts
    additional_student_ids = [_uuid() for _ in range(40)]

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

    # Add additional students for realistic enrollment numbers
    for i, student_id in enumerate(additional_student_ids):
        students.append({
            "student_id": student_id,
            "external_sis_id": f"S{1004 + i:04d}",
            "program_id": program_engineering_id,
            "campus_id": campus_main_id,
            "standing": "regular",
            "student_status": "following_plan",
            "gpa": 2.5 + (i % 20) * 0.1,  # Vary GPAs between 2.5-4.4
            "credits_completed": 30 + (i % 60),  # Vary credits 30-89
            "financial_status": "clear",
            "study_type": "paid",
            "expected_grad_term": None,
        })

    # ------------------------------------------------------------------
    # Courses
    # Engineering courses and foundation courses: introductory course (ENGR101) and
    # more advanced course (ENGR201), plus foundational courses CS101, PHYS101,
    # MATH101, PROB101, and STAT101. ENGR201 requires ENGR101 as a prerequisite.
    course_a_id = _uuid()  # ENGR101
    course_b_id = _uuid()  # ENGR201
    course_cs101_id = _uuid()  # CS101
    course_phys101_id = _uuid()  # PHYS101
    course_math101_id = _uuid()  # MATH101
    course_prob101_id = _uuid()  # PROB101
    course_stat101_id = _uuid()  # STAT101
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
        {
            "course_id": course_cs101_id,
            "code": "CS101",
            "title": "Introduction to Computer Science",
            "credits": 3,
            "department_id": _uuid(),
            "level": 100,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
        {
            "course_id": course_phys101_id,
            "code": "PHYS101",
            "title": "General Physics I",
            "credits": 4,
            "department_id": _uuid(),
            "level": 100,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
        {
            "course_id": course_math101_id,
            "code": "MATH101",
            "title": "Calculus I",
            "credits": 4,
            "department_id": _uuid(),
            "level": 100,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
        {
            "course_id": course_prob101_id,
            "code": "PROB101",
            "title": "Probability Theory",
            "credits": 3,
            "department_id": _uuid(),
            "level": 100,
            "course_type": "major",
            "semester_pattern": "both",
            "delivery_mode": "in_person",
            "campus_id": campus_main_id,
        },
        {
            "course_id": course_stat101_id,
            "code": "STAT101",
            "title": "Introduction to Statistics",
            "credits": 3,
            "department_id": _uuid(),
            "level": 100,
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
    # Create multiple classrooms named after famous scientists on the main campus.
    room_einstein_id = _uuid()
    room_curie_id = _uuid()
    room_newton_id = _uuid()
    room_darwin_id = _uuid()
    room_tesla_id = _uuid()
    room_pasteur_id = _uuid()
    room_galileo_id = _uuid()
    room_feynman_id = _uuid()
    room_hawking_id = _uuid()
    room_faraday_id = _uuid()
    room_mendel_id = _uuid()
    room_bohr_id = _uuid()
    campus_rooms = [
        {
            "room_id": room_einstein_id,
            "campus_id": campus_main_id,
            "name": "Einstein 1-01",
            "capacity": 45,
        },
        {
            "room_id": room_curie_id,
            "campus_id": campus_main_id,
            "name": "Curie 1-02",
            "capacity": 40,
        },
        {
            "room_id": room_newton_id,
            "campus_id": campus_main_id,
            "name": "Newton 2-03",
            "capacity": 50,
        },
        {
            "room_id": room_darwin_id,
            "campus_id": campus_main_id,
            "name": "Darwin 2-04",
            "capacity": 35,
        },
        {
            "room_id": room_tesla_id,
            "campus_id": campus_main_id,
            "name": "Tesla 2-05",
            "capacity": 42,
        },
        {
            "room_id": room_pasteur_id,
            "campus_id": campus_main_id,
            "name": "Pasteur 3-06",
            "capacity": 38,
        },
        {
            "room_id": room_galileo_id,
            "campus_id": campus_main_id,
            "name": "Galileo 3-07",
            "capacity": 46,
        },
        {
            "room_id": room_feynman_id,
            "campus_id": campus_main_id,
            "name": "Feynman 3-08",
            "capacity": 44,
        },
        {
            "room_id": room_hawking_id,
            "campus_id": campus_main_id,
            "name": "Hawking 4-09",
            "capacity": 48,
        },
        {
            "room_id": room_faraday_id,
            "campus_id": campus_main_id,
            "name": "Faraday 4-10",
            "capacity": 41,
        },
        {
            "room_id": room_mendel_id,
            "campus_id": campus_main_id,
            "name": "Mendel 4-11",
            "capacity": 39,
        },
        {
            "room_id": room_bohr_id,
            "campus_id": campus_main_id,
            "name": "Bohr 5-12",
            "capacity": 43,
        },
    ]

    # ------------------------------------------------------------------
    # Instructors
    # Multiple instructors for different courses. Their schedules are kept empty
    # here; the agent can populate ``instructor_schedule`` as needed.
    instructor_ahmad_id = _uuid()
    instructor_layla_id = _uuid()
    instructor_omar_id = _uuid()
    instructor_sara_id = _uuid()
    instructor_hassan_id = _uuid()
    instructor_fatma_id = _uuid()
    instructor_kareem_id = _uuid()
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
        {
            "instructor_id": instructor_omar_id,
            "name": "Dr. Omar Al-Rashid",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
        {
            "instructor_id": instructor_sara_id,
            "name": "Prof. Sara Qasemi",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
        {
            "instructor_id": instructor_hassan_id,
            "name": "Dr. Hassan Nouri",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
        {
            "instructor_id": instructor_fatma_id,
            "name": "Dr. Fatma Al-Zaidi",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
        {
            "instructor_id": instructor_kareem_id,
            "name": "Prof. Kareem Mansouri",
            "department_id": _uuid(),
            "campus_id": campus_main_id,
        },
    ]

    instructor_schedule: list = []

    # ------------------------------------------------------------------
    # Sections and meetings
    # Course A has two sections at different times.  Course B has two
    # sections - one that overlaps with Sarah's existing class and one
    # that doesn't conflict.  Each section references the campus
    # and an instructor. New courses have 2+ sections each with high capacity.
    section_a1_id = _uuid()
    section_a2_id = _uuid()
    section_b1_id = _uuid()
    section_b2_id = _uuid()  # New ENGR201 section on Tuesday

    # CS101 sections
    section_cs101_1_id = _uuid()
    section_cs101_2_id = _uuid()
    section_cs101_3_id = _uuid()

    # PHYS101 sections
    section_phys101_1_id = _uuid()
    section_phys101_2_id = _uuid()

    # MATH101 sections
    section_math101_1_id = _uuid()
    section_math101_2_id = _uuid()
    section_math101_3_id = _uuid()

    # PROB101 sections
    section_prob101_1_id = _uuid()
    section_prob101_2_id = _uuid()

    # STAT101 sections
    section_stat101_1_id = _uuid()
    section_stat101_2_id = _uuid()

    sections = [
        {
            "section_id": section_a1_id,
            "course_id": course_a_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_ahmad_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_a2_id,
            "course_id": course_a_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_layla_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_b1_id,
            "course_id": course_b_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_ahmad_id,
            "capacity": 30,
            "waitlist_capacity": 5,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_b2_id,
            "course_id": course_b_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",  # ENGR201 section S02
            "instructor_id": instructor_layla_id,
            "capacity": 25,
            "waitlist_capacity": 3,
            "campus_id": campus_main_id,
        },
        # CS101 sections
        {
            "section_id": section_cs101_1_id,
            "course_id": course_cs101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_omar_id,
            "capacity": 60,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_cs101_2_id,
            "course_id": course_cs101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_sara_id,
            "capacity": 60,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_cs101_3_id,
            "course_id": course_cs101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S03",
            "instructor_id": instructor_hassan_id,
            "capacity": 50,
            "waitlist_capacity": 8,
            "campus_id": campus_main_id,
        },
        # PHYS101 sections
        {
            "section_id": section_phys101_1_id,
            "course_id": course_phys101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_fatma_id,
            "capacity": 55,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_phys101_2_id,
            "course_id": course_phys101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_kareem_id,
            "capacity": 55,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
        # MATH101 sections
        {
            "section_id": section_math101_1_id,
            "course_id": course_math101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_omar_id,
            "capacity": 70,
            "waitlist_capacity": 15,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_math101_2_id,
            "course_id": course_math101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_sara_id,
            "capacity": 70,
            "waitlist_capacity": 15,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_math101_3_id,
            "course_id": course_math101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S03",
            "instructor_id": instructor_hassan_id,
            "capacity": 65,
            "waitlist_capacity": 12,
            "campus_id": campus_main_id,
        },
        # PROB101 sections
        {
            "section_id": section_prob101_1_id,
            "course_id": course_prob101_id,
            "term_id": term_fall_2025_id,
            "section_code": "01",
            "instructor_id": instructor_fatma_id,
            "capacity": 45,
            "waitlist_capacity": 8,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_prob101_2_id,
            "course_id": course_prob101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_kareem_id,
            "capacity": 45,
            "waitlist_capacity": 8,
            "campus_id": campus_main_id,
        },
        # STAT101 sections
        {
            "section_id": section_stat101_1_id,
            "course_id": course_stat101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S01",
            "instructor_id": instructor_ahmad_id,
            "capacity": 50,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
        {
            "section_id": section_stat101_2_id,
            "course_id": course_stat101_id,
            "term_id": term_fall_2025_id,
            "section_code": "S02",
            "instructor_id": instructor_layla_id,
            "capacity": 50,
            "waitlist_capacity": 10,
            "campus_id": campus_main_id,
        },
    ]

    # Each section has meeting blocks as specified.  ENGR101 A1 has
    # meetings on both Monday and Wednesday.  The conflict occurs on
    # Monday when ENGR101 A1 runs from 10:00–11:30 and ENGR201 B1
    # runs from 10:30–12:00.  ENGR201 A2 is available on Tuesday with
    # no conflicts.  Meetings reference the ``room_id``.
    section_meetings = [
        # ENGR101 A1 - Monday meeting
        {
            "meeting_id": _uuid(),
            "section_id": section_a1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday (Python weekday: Monday=0)
            "time_range": _tsrange(time(10, 0), time(11, 30)),
            "room_id": room_einstein_id,
        },
        # ENGR101 A1 - Wednesday meeting
        {
            "meeting_id": _uuid(),
            "section_id": section_a1_id,
            "activity": "LEC",
            "day_of_week": 2,  # Wednesday (Python weekday: Wednesday=2)
            "time_range": _tsrange(time(14, 0), time(15, 30)),
            "room_id": room_einstein_id,
        },
        # ENGR101 A2 - Wednesday (unchanged for now)
        {
            "meeting_id": _uuid(),
            "section_id": section_a2_id,
            "activity": "LEC",
            "day_of_week": 2,  # Wednesday (Python weekday: Wednesday=2)
            "time_range": _tsrange(time(14, 0), time(15, 15)),
            "room_id": room_curie_id,
        },
        # ENGR201 B1 - Monday (conflicting section)
        {
            "meeting_id": _uuid(),
            "section_id": section_b1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday (Python weekday: Monday=0)
            "time_range": _tsrange(time(10, 30), time(12, 0)),
            "room_id": room_newton_id,
        },
        # ENGR201 A2 - Tuesday (non-conflicting alternative)
        {
            "meeting_id": _uuid(),
            "section_id": section_b2_id,
            "activity": "LEC",
            "day_of_week": 1,  # Tuesday (Python weekday: Tuesday=1)
            "time_range": _tsrange(time(9, 30), time(11, 0)),
            "room_id": room_darwin_id,
        },

        # CS101 sections - distributed across different days and times
        # CS101-01 - Monday 10:30-12:00 (conflicts with ENGR101 S01 Monday 10:00-11:30)
        {
            "meeting_id": _uuid(),
            "section_id": section_cs101_1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday (Python weekday: Monday=0)
            "time_range": _tsrange(time(10, 30), time(12, 0)),
            "room_id": room_tesla_id,
        },
        # CS101-02 - Tuesday 13:00-14:30 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_cs101_2_id,
            "activity": "LEC",
            "day_of_week": 1,  # Tuesday (Python weekday: Tuesday=1)
            "time_range": _tsrange(time(13, 0), time(14, 30)),
            "room_id": room_pasteur_id,
        },
        # CS101-03 - Thursday 10:00-12:00 (2 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_cs101_3_id,
            "activity": "LEC",
            "day_of_week": 3,  # Thursday (Python weekday: Thursday=3)
            "time_range": _tsrange(time(10, 0), time(12, 0)),
            "room_id": room_galileo_id,
        },

        # PHYS101 sections
        # PHYS101-01 - Monday 8:00-9:30 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_phys101_1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday (Python weekday: Monday=0)
            "time_range": _tsrange(time(8, 0), time(9, 30)),
            "room_id": room_feynman_id,
        },
        # PHYS101-02 - Wednesday 11:00-13:00 (2 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_phys101_2_id,
            "activity": "LEC",
            "day_of_week": 2,  # Wednesday (Python weekday: Wednesday=2)
            "time_range": _tsrange(time(11, 0), time(13, 0)),
            "room_id": room_hawking_id,
        },

        # MATH101 sections
        # MATH101-01 - Sunday 11:30-13:00 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_math101_1_id,
            "activity": "LEC",
            "day_of_week": 6,  # Sunday (Python weekday: Sunday=6)
            "time_range": _tsrange(time(11, 30), time(13, 0)),
            "room_id": room_faraday_id,
        },
        # MATH101-02 - Tuesday 14:30-16:30 (2 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_math101_2_id,
            "activity": "LEC",
            "day_of_week": 1,  # Tuesday (Python weekday: Tuesday=1)
            "time_range": _tsrange(time(14, 30), time(16, 30)),
            "room_id": room_mendel_id,
        },
        # MATH101-03 - Thursday 13:00-14:30 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_math101_3_id,
            "activity": "LEC",
            "day_of_week": 3,  # Thursday (Python weekday: Thursday=3)
            "time_range": _tsrange(time(13, 0), time(14, 30)),
            "room_id": room_bohr_id,
        },

        # PROB101 sections
        # PROB101-01 - Monday 12:30-14:30 (2 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_prob101_1_id,
            "activity": "LEC",
            "day_of_week": 0,  # Monday (Python weekday: Monday=0)
            "time_range": _tsrange(time(12, 30), time(14, 30)),
            "room_id": room_curie_id,
        },
        # PROB101-02 - Wednesday 9:00-10:30 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_prob101_2_id,
            "activity": "LEC",
            "day_of_week": 2,  # Wednesday (Python weekday: Wednesday=2)
            "time_range": _tsrange(time(9, 0), time(10, 30)),
            "room_id": room_tesla_id,
        },

        # STAT101 sections
        # STAT101-01 - Sunday 14:00-16:00 (2 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_stat101_1_id,
            "activity": "LEC",
            "day_of_week": 6,  # Sunday (Python weekday: Sunday=6)
            "time_range": _tsrange(time(14, 0), time(16, 0)),
            "room_id": room_pasteur_id,
        },
        # STAT101-02 - Thursday 8:00-9:30 (1.5 hours)
        {
            "meeting_id": _uuid(),
            "section_id": section_stat101_2_id,
            "activity": "LEC",
            "day_of_week": 3,  # Thursday (Python weekday: Thursday=3)
            "time_range": _tsrange(time(8, 0), time(9, 30)),
            "room_id": room_galileo_id,
        },
    ]
    # ------------------------------------------------------------------
    # Initial enrollments
    # Create realistic enrollment numbers for all sections.
    # Sarah is enrolled in ENGR101 A1, plus additional students to reach
    # 25-75% capacity in each section for realistic testing.
    enrollment = [
        # Sarah's enrollment (our main test student)
        {
            "enrollment_id": _uuid(),
            "student_id": student_sarah_id,
            "section_id": section_a1_id,
            "status": "registered",
            "enrolled_at": now,
        },
    ]

    # Distribute additional students across sections
    # ENGR101 A1: Sarah + 14 more = 15/30 (50%)
    # ENGR101 A2: 20/30 (67%)
    # ENGR201 B1: 9/30 (30%)
    # ENGR201 A2: 12/25 (48%)

    student_idx = 0

    # ENGR101 A1: Add 14 more students (Sarah already enrolled)
    for _ in range(14):
        if student_idx < len(additional_student_ids):
            enrollment.append({
                "enrollment_id": _uuid(),
                "student_id": additional_student_ids[student_idx],
                "section_id": section_a1_id,
                "status": "registered",
                "enrolled_at": now - timedelta(days=student_idx % 30),
            })
            student_idx += 1

    # ENGR101 A2: Add 20 students
    for _ in range(20):
        if student_idx < len(additional_student_ids):
            enrollment.append({
                "enrollment_id": _uuid(),
                "student_id": additional_student_ids[student_idx],
                "section_id": section_a2_id,
                "status": "registered",
                "enrolled_at": now - timedelta(days=student_idx % 30),
            })
            student_idx += 1

    # ENGR201 B1: Add 9 students
    for _ in range(9):
        if student_idx < len(additional_student_ids):
            enrollment.append({
                "enrollment_id": _uuid(),
                "student_id": additional_student_ids[student_idx],
                "section_id": section_b1_id,
                "status": "registered",
                "enrolled_at": now - timedelta(days=student_idx % 30),
            })
            student_idx += 1

    # ENGR201 A2: Add 12 students
    for _ in range(12):
        if student_idx < len(additional_student_ids):
            enrollment.append({
                "enrollment_id": _uuid(),
                "student_id": additional_student_ids[student_idx],
                "section_id": section_b2_id,
                "status": "registered",
                "enrolled_at": now - timedelta(days=student_idx % 30),
            })
            student_idx += 1

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
