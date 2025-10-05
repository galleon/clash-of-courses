"""LangGraph student tools - Business logic and database operations."""

import uuid
import logging
from datetime import datetime
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import text

from brs_backend.database.connection import get_db
from brs_backend.models.tool_outputs import (
    AttachabilityResponse,
    ConflictItem,
    EnrollmentResponse,
    ScheduleItem,
    StudentSchedule,
    Violation,
)
from brs_backend.utils.calendar_utils import get_term_dates


@tool
def get_current_schedule(
    student_id: str, format_type: str = "structured"
) -> StudentSchedule:
    """Get current schedule for a student with structured format.

    Args:
        student_id: ID of the student
        format_type: Format type ('structured', 'ical', 'basic')

    Returns:
        StudentSchedule with detailed course information
    """
    db = next(get_db())

    query = """
    SELECT
        c.code as course_code,
        c.title as course_title,
        s.section_code,
        c.credits,
        i.name as instructor,
        sm.day_of_week,
        sm.time_range,
        cr.name as room_name,
        sm.activity,
        'enrolled' as status
    FROM enrollment e
    JOIN section s ON e.section_id = s.section_id
    JOIN course c ON s.course_id = c.course_id
    JOIN instructor i ON s.instructor_id = i.instructor_id
    LEFT JOIN section_meeting sm ON s.section_id = sm.section_id
    LEFT JOIN campus_room cr ON sm.room_id = cr.room_id
    WHERE e.student_id = :student_id
    ORDER BY c.code, sm.day_of_week, sm.time_range
    """

    result = db.execute(text(query), {"student_id": student_id})
    rows = result.fetchall()

    if not rows:
        return StudentSchedule(
            student_id=student_id,
            schedule=[],
            total_credits=0,
            course_count=0,
            term="Fall 2024",
            last_updated=datetime.now(),
        )

    # Group by course
    courses = {}
    total_credits = 0

    for row in rows:
        course_key = f"{row.course_code}-{row.section_code}"

        if course_key not in courses:
            courses[course_key] = {
                "course_code": row.course_code,
                "course_title": row.course_title,
                "section_code": row.section_code,
                "credits": row.credits,
                "instructor": row.instructor,
                "status": row.status,
                "meetings": [],
            }
            total_credits += row.credits

        if row.day_of_week is not None:
            # Parse time_range (TSRANGE format: [HH:MM:SS,HH:MM:SS))
            start_time = end_time = "TBD"
            if row.time_range:
                time_str = str(row.time_range)
                # Extract times from TSRANGE format like [09:00:00,10:30:00)
                if "," in time_str:
                    times = time_str.strip("[]()").split(",")
                    if len(times) == 2:
                        start_time = times[0].strip()
                        end_time = times[1].strip()

            meeting = {
                "day": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ][row.day_of_week],
                "start_time": start_time,
                "end_time": end_time,
                "room": row.room_name if row.room_name else "TBD",
            }
            courses[course_key]["meetings"].append(meeting)

    # Convert to ScheduleItem objects
    schedule_items = []
    for course_data in courses.values():
        item = ScheduleItem(
            course_code=course_data["course_code"],
            course_title=course_data["course_title"],
            section_code=course_data["section_code"],
            credits=course_data["credits"],
            instructor=course_data["instructor"],
            status=course_data["status"],
            meetings=course_data["meetings"],
        )
        schedule_items.append(item)

    return StudentSchedule(
        student_id=student_id,
        term_id="fall_2024",
        schedule=schedule_items,
        total_credits=total_credits,
        pending_credits=0,  # No pending credits for enrolled courses
        course_count=len(courses),
        pending_count=0,  # No pending courses for enrolled courses
    )


@tool
def check_course_attachability(
    student_id: str, course_code: str, section_code: str
) -> AttachabilityResponse:
    """Check if a student can enroll in a specific course section.

    Args:
        student_id: ID of the student
        course_code: Course code (e.g., 'CS101')
        section_code: Section code (e.g., 'A1')

    Returns:
        AttachabilityResponse with enrollment eligibility details
    """
    db = next(get_db())

    # Get section details
    section_query = """
    SELECT s.section_id, s.capacity, c.title, c.credits,
           i.name as instructor,
           COALESCE(e.enrolled_count, 0) as enrolled_count
    FROM section s
    JOIN course c ON s.course_id = c.course_id
    JOIN instructor i ON s.instructor_id = i.instructor_id
    LEFT JOIN (
        SELECT section_id, COUNT(*) as enrolled_count
        FROM enrollment
        GROUP BY section_id
    ) e ON s.section_id = e.section_id
    WHERE c.code = :course_code AND s.section_code = :section_code
    """

    result = db.execute(
        text(section_query), {"course_code": course_code, "section_code": section_code}
    )
    section = result.fetchone()

    if not section:
        return AttachabilityResponse(
            success=False,
            attachable=False,
            reason="Course section not found",
            section_info={
                "course_code": course_code,
                "section_code": section_code,
                "available": False,
            },
            conflicts=[],
            recommendations=["Verify course code and section number"],
        )

    # Check capacity
    available_spots = section.capacity - section.enrolled_count
    if available_spots <= 0:
        return AttachabilityResponse(
            success=False,
            attachable=False,
            reason="Section is full",
            section_info={
                "course_code": course_code,
                "section_code": section_code,
                "title": section.title,
                "instructor": section.instructor,
                "capacity": section.capacity,
                "enrolled": section.enrolled_count,
                "available": False,
            },
            conflicts=[],
            recommendations=[
                "Consider a different section",
                "Join waitlist if available",
            ],
        )

    # Check prerequisites FIRST - students must complete required courses before enrolling
    prereq_query = """
    SELECT c2.code as prereq_code, cp.type
    FROM course_prereq cp
    JOIN course c1 ON cp.course_id = c1.course_id
    JOIN course c2 ON cp.req_course_id = c2.course_id
    WHERE c1.code = :course_code
    """

    result = db.execute(text(prereq_query), {"course_code": course_code})
    prerequisites = result.fetchall()

    if prerequisites:
        # Check if student has completed all prerequisites
        for prereq in prerequisites:
            # Check if student has completed this prerequisite course
            completed_query = """
            SELECT 1 FROM enrollment e
            JOIN section s ON e.section_id = s.section_id
            JOIN course c ON s.course_id = c.course_id
            WHERE e.student_id = :student_id AND c.code = :prereq_code AND e.status = 'completed'
            """

            result = db.execute(
                text(completed_query),
                {"student_id": student_id, "prereq_code": prereq.prereq_code},
            )
            completed = result.fetchone()

            if not completed:
                # Check if student is currently enrolled (but not completed)
                enrolled_query = """
                SELECT 1 FROM enrollment e
                JOIN section s ON e.section_id = s.section_id
                JOIN course c ON s.course_id = c.course_id
                WHERE e.student_id = :student_id AND c.code = :prereq_code AND e.status = 'registered'
                """

                result = db.execute(
                    text(enrolled_query),
                    {"student_id": student_id, "prereq_code": prereq.prereq_code},
                )
                currently_enrolled = result.fetchone()

                if currently_enrolled:
                    reason = f"Prerequisite {prereq.prereq_code} must be completed before enrolling in {course_code}. You are currently enrolled in {prereq.prereq_code} but have not yet completed it."
                else:
                    reason = f"Missing prerequisite: {prereq.prereq_code} must be completed before enrolling in {course_code}"

                return AttachabilityResponse(
                    success=False,
                    attachable=False,
                    reason=reason,
                    section_info={
                        "course_code": course_code,
                        "section_code": section_code,
                        "title": section.title,
                        "available": False,
                    },
                    conflicts=[],
                    recommendations=[f"Complete {prereq.prereq_code} first"],
                    violations=[
                        Violation(
                            rule_code="PREREQUISITE_NOT_COMPLETED",
                            message=f"Prerequisite {prereq.prereq_code} not completed",
                            severity="error",
                        )
                    ],
                )

    # Check for existing enrollment
    enrollment_query = """
    SELECT 1 FROM enrollment e
    JOIN section s ON e.section_id = s.section_id
    JOIN course c ON s.course_id = c.course_id
    WHERE e.student_id = :student_id AND c.code = :course_code
    """

    result = db.execute(
        text(enrollment_query), {"student_id": student_id, "course_code": course_code}
    )
    existing = result.fetchone()

    if existing:
        return AttachabilityResponse(
            success=False,
            attachable=False,
            reason="Already enrolled in this course",
            section_info={
                "course_code": course_code,
                "section_code": section_code,
                "title": section.title,
                "available": False,
            },
            conflicts=[],
            recommendations=["Drop current section before enrolling in new one"],
        )

    # Check for schedule conflicts
    current_schedule = get_current_schedule.invoke({"student_id": student_id})
    conflicts = []

    # Get meeting times for the target section
    meeting_query = """
    SELECT day_of_week, time_range, room_id, activity
    FROM section_meeting
    WHERE section_id = :section_id
    """

    result = db.execute(text(meeting_query), {"section_id": section.section_id})
    target_meetings = result.fetchall()

    # Check conflicts with current schedule (simplified for now)
    conflicts = []
    # TODO: Implement proper time conflict checking with time_range fields

    # For now, just check basic eligibility - no conflicts
    attachable = len(conflicts) == 0
    reason = "Eligible for enrollment" if attachable else "Schedule conflicts detected"

    recommendations = []
    if not attachable:
        recommendations.extend(
            [
                "Resolve schedule conflicts first",
                "Consider dropping conflicting courses",
                "Look for alternative sections",
            ]
        )
    else:
        recommendations.append("Ready to enroll")

    return AttachabilityResponse(
        success=True,
        attachable=attachable,
        reason=reason,
        section_info={
            "course_code": course_code,
            "section_code": section_code,
            "title": section.title,
            "instructor": section.instructor,
            "credits": section.credits,
            "capacity": section.capacity,
            "enrolled": section.enrolled_count,
            "available_spots": available_spots,
            "available": attachable,
        },
        conflicts=conflicts,
        recommendations=recommendations,
    )


@tool
def enroll_in_course(
    student_id: str,
    course_code: str,
    section_code: str,
    auto_check: bool = True,
    auto_resolve_conflicts: bool = True,
) -> EnrollmentResponse:
    """Enroll a student in a course section with intelligent conflict resolution.

    Args:
        student_id: ID of the student
        course_code: Course code (e.g., 'CS101')
        section_code: Section code (e.g., 'A1')
        auto_check: Whether to perform attachability check first
        auto_resolve_conflicts: Whether to automatically find alternative sections if conflicts exist

    Returns:
        EnrollmentResponse with enrollment result and updated schedule
    """
    db = next(get_db())

    # Step 1: Perform attachability check if requested (prerequisites + basic validation)
    if auto_check:
        attachability = check_course_attachability.invoke(
            {
                "student_id": student_id,
                "course_code": course_code,
                "section_code": section_code,
            }
        )
        if not attachability.attachable:
            return EnrollmentResponse(
                success=False,
                message=f"Cannot enroll: {attachability.reason}",
                enrollment_id=None,
                updated_schedule=get_current_schedule.invoke(
                    {"student_id": student_id}
                ),
                conflicts=attachability.conflicts,
                transaction_id=str(uuid.uuid4()),
            )

    try:
        # Step 2: Get requested section details
        section_query = """
        SELECT s.section_id, c.credits, c.title, s.capacity,
               COUNT(e.enrollment_id) as current_enrollment
        FROM section s
        JOIN course c ON s.course_id = c.course_id
        LEFT JOIN enrollment e ON s.section_id = e.section_id AND e.status = 'registered'
        WHERE c.code = :course_code AND s.section_code = :section_code
        GROUP BY s.section_id, c.credits, c.title, s.capacity
        """

        result = db.execute(
            text(section_query),
            {"course_code": course_code, "section_code": section_code},
        )
        section = result.fetchone()

        if not section:
            return EnrollmentResponse(
                success=False,
                message="Course section not found",
                enrollment_id=None,
                updated_schedule=get_current_schedule.invoke(
                    {"student_id": student_id}
                ),
                conflicts=[],
                transaction_id=str(uuid.uuid4()),
            )

        # Step 3: Check if requested section has capacity
        if section.current_enrollment >= section.capacity:
            if auto_resolve_conflicts:
                # Find alternative sections with capacity
                alternative_section = _find_alternative_section(
                    db, student_id, course_code, section_code
                )
                if alternative_section:
                    return _enroll_in_alternative_section(
                        db, student_id, course_code, alternative_section
                    )
                else:
                    # Notify department head - all sections full
                    _notify_department_head(
                        db, student_id, course_code, "ALL_SECTIONS_FULL"
                    )

            return EnrollmentResponse(
                success=False,
                message=f"Section {section_code} is full. All sections for {course_code} are at capacity.",
                enrollment_id=None,
                updated_schedule=get_current_schedule.invoke(
                    {"student_id": student_id}
                ),
                conflicts=[],
                transaction_id=str(uuid.uuid4()),
            )

        # Step 4: Check for time conflicts with current schedule
        conflicts = _check_time_conflicts(db, student_id, section.section_id)

        if conflicts and auto_resolve_conflicts:
            # Find alternative sections without conflicts
            alternative_section = _find_alternative_section(
                db, student_id, course_code, section_code, avoid_conflicts=True
            )
            if alternative_section:
                return _enroll_in_alternative_section(
                    db,
                    student_id,
                    course_code,
                    alternative_section,
                    original_request=f"{course_code} {section_code}",
                )
            else:
                # Notify department head - conflicts prevent enrollment
                _notify_department_head(
                    db, student_id, course_code, "SCHEDULE_CONFLICTS"
                )

                return EnrollmentResponse(
                    success=False,
                    message=f"Time conflict detected with {course_code} {section_code}. No alternative sections available without conflicts.",
                    enrollment_id=None,
                    updated_schedule=get_current_schedule.invoke(
                        {"student_id": student_id}
                    ),
                    conflicts=[
                        ConflictItem(
                            type="time_conflict",
                            description=conf["description"],
                            course_code=course_code,
                            day=conf.get("day"),
                        )
                        for conf in conflicts
                    ],
                    transaction_id=str(uuid.uuid4()),
                )
        elif conflicts:
            return EnrollmentResponse(
                success=False,
                message=f"Time conflict detected with {course_code} {section_code}",
                enrollment_id=None,
                updated_schedule=get_current_schedule.invoke(
                    {"student_id": student_id}
                ),
                conflicts=[
                    ConflictItem(
                        type="time_conflict",
                        description=conf["description"],
                        course_code=course_code,
                        day=conf.get("day"),
                    )
                    for conf in conflicts
                ],
                transaction_id=str(uuid.uuid4()),
            )

        # Step 5: Proceed with enrollment in requested section
        return _complete_enrollment(
            db, student_id, section.section_id, f"{course_code} {section_code}"
        )

    except Exception as e:
        db.rollback()
        return EnrollmentResponse(
            success=False,
            message=f"Enrollment failed: {str(e)}",
            enrollment_id=None,
            updated_schedule=get_current_schedule.invoke({"student_id": student_id}),
            conflicts=[],
            transaction_id=str(uuid.uuid4()),
        )


@tool
def drop_course(student_id: str, course_code: str) -> EnrollmentResponse:
    """Drop a student from a course.

    Args:
        student_id: ID of the student
        course_code: Course code to drop

    Returns:
        EnrollmentResponse with drop result and updated schedule
    """
    db = next(get_db())

    try:
        # Find enrollment
        enrollment_query = """
        SELECT e.enrollment_id, s.section_id FROM enrollment e
        JOIN section s ON e.section_id = s.section_id
        JOIN course c ON s.course_id = c.course_id
        WHERE e.student_id = :student_id AND c.code = :course_code
        """

        result = db.execute(
            text(enrollment_query),
            {"student_id": student_id, "course_code": course_code},
        )
        enrollment = result.fetchone()

        if not enrollment:
            return EnrollmentResponse(
                success=False,
                message=f"Not enrolled in {course_code}",
                enrollment_id=None,
                updated_schedule=get_current_schedule(student_id),
                conflicts=[],
                transaction_id=str(uuid.uuid4()),
            )

        # Delete enrollment
        delete_query = "DELETE FROM enrollment WHERE enrollment_id = :enrollment_id"
        db.execute(text(delete_query), {"enrollment_id": enrollment.enrollment_id})

        # No need to update enrolled count - it's calculated dynamically

        db.commit()

        # Get updated schedule
        updated_schedule = get_current_schedule(student_id)

        return EnrollmentResponse(
            success=True,
            message=f"Successfully dropped {course_code}",
            enrollment_id=enrollment.enrollment_id,
            updated_schedule=updated_schedule,
            conflicts=[],
            transaction_id=str(uuid.uuid4()),
        )

    except Exception as e:
        db.rollback()
        return EnrollmentResponse(
            success=False,
            message=f"Drop failed: {str(e)}",
            enrollment_id=None,
            updated_schedule=get_current_schedule(student_id),
            conflicts=[],
            transaction_id=str(uuid.uuid4()),
        )


@tool
def get_schedule_ical(student_id: str) -> dict[str, Any]:
    """Get student schedule in iCal format.

    Args:
        student_id: ID of the student

    Returns:
        Dictionary with iCal string and metadata
    """
    from brs_backend.utils.calendar_utils import schedule_to_ical

    schedule = get_current_schedule.invoke({"student_id": student_id})
    term_start, _ = get_term_dates()

    ical_string = schedule_to_ical(schedule, term_start)

    return {
        "ical_content": ical_string,
        "student_id": student_id,
        "course_count": schedule.course_count,
        "total_credits": schedule.total_credits,
        "term": schedule.term,
        "generated_at": datetime.now().isoformat(),
    }


@tool
def search_available_courses(
    query: str = None, department: str = None, level: str = None
) -> list[dict[str, Any]]:
    """Search for available courses with filters.

    Args:
        query: Text search query
        department: Department code filter
        level: Course level filter (100, 200, etc.)

    Returns:
        List of available course information
    """
    db = next(get_db())

    base_query = """
    SELECT DISTINCT c.code, c.title, c.credits, c.level, c.course_type,
           c.semester_pattern, c.delivery_mode, s.section_code,
           i.name as instructor_name, s.capacity,
           COALESCE(e.enrolled_count, 0) as enrolled_count
    FROM course c
    JOIN section s ON c.course_id = s.course_id
    JOIN instructor i ON s.instructor_id = i.instructor_id
    LEFT JOIN (
        SELECT section_id, COUNT(*) as enrolled_count
        FROM enrollment
        GROUP BY section_id
    ) e ON s.section_id = e.section_id
    WHERE s.capacity > COALESCE(e.enrolled_count, 0)
    """

    conditions = []
    params = []

    if query:
        conditions.append("(c.title ILIKE %s OR c.code ILIKE %s)")
        params.extend([f"%{query}%", f"%{query}%"])

    if level:
        conditions.append("c.level = %s")
        params.append(int(level))

    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    base_query += " ORDER BY c.code"

    result = db.execute(text(base_query), params)
    rows = result.fetchall()

    courses = []
    for row in rows:
        courses.append(
            {
                "course_code": row.code,
                "title": row.title,
                "credits": row.credits,
                "level": row.level,
                "course_type": row.course_type,
                "semester_pattern": row.semester_pattern,
                "delivery_mode": row.delivery_mode,
                "section_code": row.section_code,
                "instructor_name": row.instructor_name,
                "capacity": row.capacity,
                "enrolled_count": row.enrolled_count,
                "available_spots": row.capacity - row.enrolled_count,
            }
        )

    return courses


# Helper functions for complex enrollment workflow


def _check_time_conflicts(db, student_id: str, target_section_id: str) -> list[dict]:
    """Check for time conflicts between target section and student's current schedule."""
    conflicts = []

    # Get target section meeting times
    target_meetings_query = """
    SELECT day_of_week, time_range
    FROM section_meeting
    WHERE section_id = :section_id
    """
    target_meetings = db.execute(
        text(target_meetings_query), {"section_id": target_section_id}
    ).fetchall()

    # Get student's current meeting times
    current_meetings_query = """
    SELECT sm.day_of_week, sm.time_range, c.code as course_code
    FROM enrollment e
    JOIN section s ON e.section_id = s.section_id
    JOIN section_meeting sm ON s.section_id = sm.section_id
    JOIN course c ON s.course_id = c.course_id
    WHERE e.student_id = :student_id AND e.status = 'registered'
    """
    current_meetings = db.execute(
        text(current_meetings_query), {"student_id": student_id}
    ).fetchall()

    # Check for conflicts (simplified - same day overlap)
    for target_meeting in target_meetings:
        for current_meeting in current_meetings:
            if target_meeting.day_of_week == current_meeting.day_of_week:
                conflicts.append(
                    {
                        "description": f"Time conflict on {target_meeting.day_of_week} with {current_meeting.course_code}",
                        "day": target_meeting.day_of_week,
                        "conflicting_course": current_meeting.course_code,
                    }
                )

    return conflicts


def _find_alternative_section(
    db,
    student_id: str,
    course_code: str,
    requested_section: str,
    avoid_conflicts: bool = False,
):
    """Find alternative sections for a course that have capacity and optionally no conflicts."""

    # Get all sections for the course except the requested one
    sections_query = """
    SELECT s.section_id, s.section_code, s.capacity,
           COUNT(e.enrollment_id) as current_enrollment
    FROM section s
    JOIN course c ON s.course_id = c.course_id
    LEFT JOIN enrollment e ON s.section_id = e.section_id AND e.status = 'registered'
    WHERE c.code = :course_code AND s.section_code != :requested_section
    GROUP BY s.section_id, s.section_code, s.capacity
    HAVING COUNT(e.enrollment_id) < s.capacity
    ORDER BY s.section_code
    """

    alternative_sections = db.execute(
        text(sections_query),
        {"course_code": course_code, "requested_section": requested_section},
    ).fetchall()

    # If we need to avoid conflicts, check each section
    if avoid_conflicts:
        for section in alternative_sections:
            conflicts = _check_time_conflicts(db, student_id, section.section_id)
            if not conflicts:  # No conflicts found
                return {
                    "section_id": section.section_id,
                    "section_code": section.section_code,
                    "available_spots": section.capacity - section.current_enrollment,
                }
        return None  # No conflict-free sections found

    # Return first available section if not checking conflicts
    if alternative_sections:
        section = alternative_sections[0]
        return {
            "section_id": section.section_id,
            "section_code": section.section_code,
            "available_spots": section.capacity - section.current_enrollment,
        }

    return None


def _enroll_in_alternative_section(
    db,
    student_id: str,
    course_code: str,
    alternative_section: dict,
    original_request: str = None,
):
    """Complete enrollment in an alternative section."""
    section_id = alternative_section["section_id"]
    section_code = alternative_section["section_code"]

    enrollment_result = _complete_enrollment(
        db, student_id, section_id, f"{course_code} {section_code}"
    )

    # Update the message to indicate automatic section selection
    if enrollment_result.success and original_request:
        enrollment_result.message = (
            f"Enrolled in {course_code} {section_code} instead of {original_request} "
            f"due to conflicts/capacity. {alternative_section['available_spots']} spots remaining."
        )
    elif enrollment_result.success:
        enrollment_result.message = (
            f"Enrolled in {course_code} {section_code}. "
            f"{alternative_section['available_spots']} spots remaining."
        )

    return enrollment_result


def _complete_enrollment(db, student_id: str, section_id: str, course_section: str):
    """Complete the actual enrollment process."""
    try:
        enrollment_id = str(uuid.uuid4())
        enrollment_query = """
        INSERT INTO enrollment (enrollment_id, student_id, section_id, status)
        VALUES (:enrollment_id, :student_id, :section_id, 'registered')
        RETURNING enrollment_id
        """

        result = db.execute(
            text(enrollment_query),
            {
                "enrollment_id": enrollment_id,
                "student_id": student_id,
                "section_id": section_id,
            },
        )
        enrollment_id = str(result.fetchone().enrollment_id)
        db.commit()

        updated_schedule = get_current_schedule.invoke({"student_id": student_id})

        return EnrollmentResponse(
            success=True,
            message=f"Successfully enrolled in {course_section}",
            enrollment_id=enrollment_id,
            updated_schedule=updated_schedule,
            conflicts=[],
            transaction_id=str(uuid.uuid4()),
        )
    except Exception as e:
        db.rollback()
        raise e


def _notify_department_head(db, student_id: str, course_code: str, reason: str):
    """Notify department head about enrollment issues."""
    # This could send an email, create a notification, or log to a system
    # For now, we'll just log it

    # Get course department
    dept_query = """
    SELECT d.name as department_name
    FROM course c
    JOIN department d ON c.department_id = d.department_id
    WHERE c.code = :course_code
    """

    try:
        result = db.execute(text(dept_query), {"course_code": course_code})
        dept = result.fetchone()
        dept_name = dept.department_name if dept else "Unknown Department"

        logging.info(
            f"DEPARTMENT NOTIFICATION: {dept_name} - Student {student_id} cannot enroll in {course_code}. Reason: {reason}"
        )

        # TODO: Implement actual notification system
        # - Send email to department head
        # - Create database notification record
        # - Add to pending requests queue

    except Exception as e:
        logging.error(f"Failed to notify department head: {str(e)}")
