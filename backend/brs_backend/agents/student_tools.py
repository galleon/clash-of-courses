"""Student agent tools for course management - SmolAgents Enhanced V4."""

from datetime import datetime
from uuid import UUID

from smolagents import tool

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import (
    Course,
    CoursePrereq,
    Enrollment,
    RegistrationRequest,
    Section,
    SectionMeeting,
    Student,
)


def check_prerequisites(student_id: str, course_id: str) -> dict:
    """Check if student has completed prerequisites for a course.

    Args:
        student_id: UUID string of the student
        course_id: UUID string of the course to check prerequisites for

    Returns:
        Dict with success, met (bool), and missing_prerequisites list
    """
    try:
        db = SessionLocal()

        # Get all prerequisites for this course
        prerequisites = (
            db.query(CoursePrereq)
            .filter(
                CoursePrereq.course_id == UUID(course_id),
                CoursePrereq.type == "prereq"
            )
            .all()
        )

        if not prerequisites:
            return {"success": True, "met": True, "missing_prerequisites": []}

        # Get student's completed courses (enrolled with grade)
        completed_enrollments = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "completed"
            )
            .all()
        )

        completed_course_ids = {enrollment.section.course_id for enrollment in completed_enrollments}

        # Check each prerequisite
        missing_prerequisites = []
        for prereq in prerequisites:
            if prereq.req_course_id not in completed_course_ids:
                req_course = db.query(Course).filter(Course.course_id == prereq.req_course_id).first()
                if req_course:
                    missing_prerequisites.append({
                        "course_code": req_course.code,
                        "course_title": req_course.title
                    })

        return {
            "success": True,
            "met": len(missing_prerequisites) == 0,
            "missing_prerequisites": missing_prerequisites
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking prerequisites: {str(e)}",
            "met": False,
            "missing_prerequisites": []
        }
    finally:
        db.close()


def find_non_conflicting_alternatives(student_id: str, target_course_code: str, exclude_section_id: str = None) -> list:
    """Find alternative sections of the same course that don't conflict with student's schedule.

    Args:
        student_id: UUID string of the student
        target_course_code: Course code to find alternatives for (e.g., "ENGR201")
        exclude_section_id: Section ID to exclude from results (the conflicting one)

    Returns:
        List of non-conflicting section dictionaries
    """
    try:
        db = SessionLocal()

        # Get the target course
        course = db.query(Course).filter(Course.code == target_course_code).first()
        if not course:
            return []

        # Get all sections for this course
        sections_query = db.query(Section).filter(Section.course_id == course.course_id)
        if exclude_section_id:
            sections_query = sections_query.filter(Section.section_id != UUID(exclude_section_id))

        sections = sections_query.all()

        # Get student's current schedule to check for conflicts
        student_enrollments = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered"
            )
            .all()
        )

        # Get all meeting times for student's current sections
        student_meetings = []
        for enrollment in student_enrollments:
            meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == enrollment.section_id)
                .all()
            )
            student_meetings.extend(meetings)

        alternatives = []

        for section in sections:
            # Check if this section has conflicts
            section_meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == section.section_id)
                .all()
            )

            has_conflict = False
            for section_meeting in section_meetings:
                for student_meeting in student_meetings:
                    # Check for time conflicts (simplified - same day check)
                    if section_meeting.day_of_week == student_meeting.day_of_week:
                        has_conflict = True
                        break
                if has_conflict:
                    break

            if not has_conflict:
                # Get enrollment count
                enrolled_count = (
                    db.query(Enrollment)
                    .filter(
                        Enrollment.section_id == section.section_id,
                        Enrollment.status == "registered"
                    )
                    .count()
                )

                # Parse meeting times
                meeting_info = []
                for meeting in section_meetings:
                    start_time = None
                    end_time = None

                    if meeting.time_range:
                        time_str = str(meeting.time_range)
                        if '[' in time_str and ')' in time_str:
                            time_part = time_str.strip('[]()').split(',')
                            if len(time_part) == 2:
                                start_time = time_part[0].strip()
                                end_time = time_part[1].strip()

                    meeting_info.append({
                        "day_of_week": meeting.day_of_week,
                        "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][meeting.day_of_week],
                        "start_time": start_time,
                        "end_time": end_time,
                        "room": meeting.room.name if meeting.room else None,
                        "activity": meeting.activity
                    })

                alternatives.append({
                    "section_id": str(section.section_id),
                    "section_code": section.section_code,
                    "instructor": section.instructor.name if section.instructor else "TBD",
                    "capacity": section.capacity,
                    "enrolled": enrolled_count,
                    "available": section.capacity - enrolled_count,
                    "meetings": meeting_info,
                    "reason": "No schedule conflicts detected"
                })

        return alternatives

    except Exception as e:
        # Log error but don't crash - return empty list
        return []
    finally:
        db.close()


@tool
def get_student_info(student_id: str) -> dict:
    """Get basic student information including GPA, credits, and status.

    Args:
        student_id: UUID string of the student
    """
    try:
        db = SessionLocal()

        student = (
            db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        )
        if not student:
            return {"success": False, "error": "Student not found", "data": None}

        return {
            "success": True,
            "preferred_card_types": ["student_profile"],  # More specific card type
            "data": {
                "student_id": str(student.student_id),
                "external_sis_id": student.external_sis_id,
                "gpa": float(student.gpa) if student.gpa else None,
                "credits_completed": student.credits_completed,
                "standing": student.standing,
                "student_status": student.student_status,
                "financial_status": student.financial_status,
                "study_type": student.study_type,
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving student info: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


def check_pending_requests(student_id: str) -> dict:
    """Get pending registration requests for a student.

    Args:
        student_id: UUID string of the student
    """
    try:
        db = SessionLocal()

        pending_requests = (
            db.query(RegistrationRequest)
            .filter(
                RegistrationRequest.student_id == UUID(student_id),
                RegistrationRequest.state.in_(
                    ["submitted", "advisor_review", "dept_review"]
                ),
            )
            .all()
        )

        requests_data = []
        for req in pending_requests:
            # Get section and course details
            to_section = req.to_section
            from_section = req.from_section

            request_data = {
                "request_id": str(req.request_id),
                "type": req.type,
                "state": req.state,
                "reason": req.reason,
                "created_at": req.created_at.isoformat() if req.created_at else None,
            }

            if to_section:
                request_data["to_course"] = {
                    "code": to_section.course.code,
                    "title": to_section.course.title,
                    "section_code": to_section.section_code,
                }

            if from_section:
                request_data["from_course"] = {
                    "code": from_section.course.code,
                    "title": from_section.course.title,
                    "section_code": from_section.section_code,
                }

            requests_data.append(request_data)

        return {
            "success": True,
            "preferred_card_types": ["request_summary", "generic"],
            "data": {"count": len(pending_requests), "requests": requests_data},
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking pending requests: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def check_attachable(student_id: str, section_id: str) -> dict:
    """Check if a student can attach to a specific section (eligibility check).

    Priority order:
    1. Prerequisites first - if not met, reject immediately with NO alternatives
    2. Time conflicts - if conflicts exist, find alternative sections
    3. Seat availability - if alternative has seats, suggest for auto-enroll; if full, escalate

    Args:
        student_id: UUID string of the student
        section_id: UUID string of the section to check
    """
    try:
        # Validate UUID strings first
        try:
            student_uuid = UUID(student_id)
            section_uuid = UUID(section_id)
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid UUID format: {str(e)}",
                "violations": [],
                "attachable": False
            }

        db = SessionLocal()

        # Get student and section
        student = (
            db.query(Student).filter(Student.student_id == student_uuid).first()
        )
        section = (
            db.query(Section).filter(Section.section_id == section_uuid).first()
        )

        if not student:
            return {"success": False, "error": "Student not found", "violations": []}
        if not section:
            return {"success": False, "error": "Section not found", "violations": []}

        violations = []

        # STEP 1: Check prerequisites FIRST - if not met, reject immediately with NO alternatives
        prereq_check = check_prerequisites(student_id, str(section.course.course_id))
        if prereq_check["success"] and not prereq_check["met"]:
            missing_prereqs = [p["course_code"] for p in prereq_check["missing_prerequisites"]]
            violations.append(
                {
                    "rule_code": "BR-003",
                    "message": f"Missing prerequisites: {', '.join(missing_prereqs)}",
                    "severity": "error",
                }
            )

            # Return immediately with NO alternatives if prerequisites not met
            return {
                "success": True,
                "preferred_card_types": ["course_info", "generic"],
                "attachable": False,
                "violations": violations,
                "suggested_alternatives": [],  # NO alternatives offered for prerequisite failures
                "data": {
                    "section": {
                        "section_id": str(section.section_id),
                        "course_code": section.course.code,
                        "course_title": section.course.title,
                        "section_code": section.section_code,
                        "capacity": section.capacity,
                        "enrolled": 0,  # Not relevant for prereq failures
                        "available": 0,  # Not relevant for prereq failures
                    },
                    "alternatives": []  # NO alternatives for prerequisite failures
                },
            }

        # Check capacity
        enrolled_count = (
            db.query(Enrollment)
            .filter(
                Enrollment.section_id == UUID(section_id),
                Enrollment.status == "registered",
            )
            .count()
        )

        if enrolled_count >= section.capacity:
            violations.append(
                {
                    "rule_code": "BR-002",
                    "message": "Section at capacity",
                    "severity": "error",
                }
            )

        # STEP 2: Check for time conflicts with current enrollments
        student_enrollments = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered",
            )
            .all()
        )

        # Get target section meetings
        target_meetings = (
            db.query(SectionMeeting)
            .filter(SectionMeeting.section_id == UUID(section_id))
            .all()
        )

        conflicting_course = None
        for enrollment in student_enrollments:
            enrolled_meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == enrollment.section_id)
                .all()
            )

            # Check for time conflicts (simplified - would need proper TSRANGE overlap check)
            for target_meeting in target_meetings:
                for enrolled_meeting in enrolled_meetings:
                    if target_meeting.day_of_week == enrolled_meeting.day_of_week:
                        conflicting_course = enrollment.section.course.code
                        violations.append(
                            {
                                "rule_code": "BR-005",
                                "message": f"Time conflict with {enrollment.section.course.code}",
                                "severity": "error",
                            }
                        )
                        break
                if conflicting_course:
                    break
            if conflicting_course:
                break

        # Check academic standing
        if student.standing in ["probation", "suspended"]:
            violations.append(
                {
                    "rule_code": "BR-001",
                    "message": f"Student on {student.standing} - advisor approval required",
                    "severity": "warning",
                }
            )

        # STEP 3: If there are conflicts, proactively find alternatives
        # Only look for alternatives if prerequisites are satisfied
        suggested_alternatives = []
        if violations:
            # Find alternatives for the same course that don't conflict and have seats
            suggested_alternatives = find_non_conflicting_alternatives(
                student_id,
                section.course.code,
                section_id
            )

        return {
            "success": True,
            "preferred_card_types": ["alternatives", "course_info", "generic"] if violations else ["course_info", "generic"],
            "attachable": len([v for v in violations if v["severity"] == "error"]) == 0,
            "violations": violations,
            "suggested_alternatives": suggested_alternatives,
            "data": {
                "section": {
                    "section_id": str(section.section_id),
                    "course_code": section.course.code,
                    "course_title": section.course.title,
                    "section_code": section.section_code,
                    "capacity": section.capacity,
                    "enrolled": enrolled_count,
                    "available": section.capacity - enrolled_count,
                },
                "alternatives": suggested_alternatives
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking attachability: {str(e)}",
            "violations": [],
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking attachability: {str(e)}",
            "violations": [],
        }
    finally:
        db.close()


def create_automatic_enrollment(student_id: str, section_id: str, reason: str | None = None) -> dict:
    """Create automatic enrollment when all conditions are met.

    Args:
        student_id: UUID string of the student
        section_id: UUID string of the section
        reason: Optional reason for enrollment

    Returns:
        Dict with success status and enrollment details
    """
    try:
        db = SessionLocal()

        # Create enrollment record
        enrollment = Enrollment(
            student_id=UUID(student_id),
            section_id=UUID(section_id),
            status="registered",
            enrolled_at=datetime.utcnow()
        )

        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)

        # Get section details for response
        section = (
            db.query(Section)
            .join(Course, Section.course_id == Course.course_id)
            .filter(Section.section_id == UUID(section_id))
            .first()
        )

        return {
            "success": True,
            "enrollment_id": str(enrollment.enrollment_id),
            "section_code": section.section_code if section else None,
            "course_code": section.course.code if section else None,
            "course_title": section.course.title if section else None,
            "enrolled_at": enrollment.enrolled_at.isoformat(),
            "message": f"✅ Automatically enrolled in {section.course.code if section else 'course'} {section.section_code if section else 'section'}!"
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error creating automatic enrollment: {str(e)}"
        }
    finally:
        db.close()


@tool
def browse_course_catalog(term_id: str | None = None, department: str | None = None) -> dict:
    """Browse available courses in the catalog that students can register for.

    Args:
        term_id: Optional term UUID to filter by (if None, shows all terms)
        department: Optional department code to filter by (e.g. "CS", "ENGR")
    """
    try:
        db = SessionLocal()

        # Build query for courses with available sections
        query = (
            db.query(Course)
            .join(Section, Course.course_id == Section.course_id)
            .distinct()
        )

        if term_id:
            query = query.filter(Section.term_id == UUID(term_id))

        if department:
            query = query.filter(Course.code.like(f"{department}%"))

        courses = query.limit(20).all()  # Limit to prevent overwhelming response

        if not courses:
            return {
                "success": True,
                "preferred_card_types": ["course_info", "generic"],
                "data": {
                    "courses": [],
                    "message": "No courses found for the specified criteria.",
                    "total_count": 0
                }
            }

        course_list = []
        for course in courses:
            # Get sections for this course
            sections_query = db.query(Section).filter(Section.course_id == course.course_id)
            if term_id:
                sections_query = sections_query.filter(Section.term_id == UUID(term_id))

            sections = sections_query.all()

            # Get enrollment counts
            section_data = []
            for section in sections:
                enrolled_count = (
                    db.query(Enrollment)
                    .filter(
                        Enrollment.section_id == section.section_id,
                        Enrollment.status == "registered"
                    )
                    .count()
                )

                # Get meetings for this section
                meetings = (
                    db.query(SectionMeeting)
                    .filter(SectionMeeting.section_id == section.section_id)
                    .all()
                )

                meeting_info = []
                for meeting in meetings:
                    # Extract start and end times from PostgreSQL TSRANGE
                    start_time = None
                    end_time = None

                    if meeting.time_range:
                        # PostgreSQL TSRANGE format: '[09:00:00,10:30:00)'
                        # Parse the time range to extract start and end times
                        time_str = str(meeting.time_range)
                        if '[' in time_str and ')' in time_str:
                            # Remove brackets and split by comma
                            time_part = time_str.strip('[]()').split(',')
                            if len(time_part) == 2:
                                start_time = time_part[0].strip()
                                end_time = time_part[1].strip()

                    meeting_info.append({
                        "day_of_week": meeting.day_of_week,
                        "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][meeting.day_of_week],
                        "start_time": start_time,
                        "end_time": end_time,
                        "room": meeting.room.name if meeting.room else None,
                        "activity": meeting.activity
                    })

                section_data.append({
                    "section_id": str(section.section_id),
                    "section_code": section.section_code,
                    "instructor": section.instructor,
                    "capacity": section.capacity,
                    "enrolled": enrolled_count,
                    "available": section.capacity - enrolled_count,
                    "meetings": meeting_info
                })

            course_list.append({
                "course_id": str(course.course_id),
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "sections": section_data
            })

        return {
            "success": True,
            "preferred_card_types": ["course_catalog", "generic"],
            "data": {
                "courses": course_list,
                "total_count": len(course_list),
                "message": f"Found {len(course_list)} available courses."
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error browsing course catalog: {str(e)}",
            "data": None
        }
    finally:
        db.close()


@tool
def search_sections(course_code: str, term_id: str | None = None) -> dict:
    """Search for available sections of a course.

    Args:
        course_code: Course code (e.g. "CS101")
        term_id: Optional term UUID to filter by
    """
    try:
        db = SessionLocal()

        # Find course
        course = db.query(Course).filter(Course.code == course_code).first()
        if not course:
            return {
                "success": False,
                "error": f"Course {course_code} not found",
                "data": None,
            }

        # Build section query
        query = db.query(Section).filter(Section.course_id == course.course_id)
        if term_id:
            query = query.filter(Section.term_id == UUID(term_id))

        sections = query.all()

        sections_data = []
        for section in sections:
            # Get enrollment count
            enrolled_count = (
                db.query(Enrollment)
                .filter(
                    Enrollment.section_id == section.section_id,
                    Enrollment.status == "registered",
                )
                .count()
            )

            # Get meetings
            meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == section.section_id)
                .all()
            )

            meetings_data = []
            for meeting in meetings:
                # Extract start and end times from PostgreSQL TSRANGE
                start_time = None
                end_time = None

                if meeting.time_range:
                    # PostgreSQL TSRANGE format: '[09:00:00,10:30:00)'
                    # Parse the time range to extract start and end times
                    time_str = str(meeting.time_range)
                    if '[' in time_str and ')' in time_str:
                        # Remove brackets and split by comma
                        time_part = time_str.strip('[]()').split(',')
                        if len(time_part) == 2:
                            start_time = time_part[0].strip()
                            end_time = time_part[1].strip()

                meetings_data.append(
                    {
                        "day_of_week": meeting.day_of_week,
                        "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][meeting.day_of_week],
                        "start_time": start_time,
                        "end_time": end_time,
                        "activity": meeting.activity,
                        "room": meeting.room.name if meeting.room else None,
                    }
                )

            sections_data.append(
                {
                    "section_id": str(section.section_id),
                    "section_code": section.section_code,
                    "instructor": section.instructor.name
                    if section.instructor
                    else "TBD",
                    "capacity": section.capacity,
                    "enrolled": enrolled_count,
                    "available": section.capacity - enrolled_count,
                    "meetings": meetings_data,
                }
            )

        return {
            "success": True,
            "preferred_card_types": ["course_catalog", "alternatives", "generic"],
            "data": {
                "courses": [{
                    "course_id": str(course.course_id),
                    "code": course.code,
                    "title": course.title,
                    "credits": course.credits,
                    "sections": sections_data
                }],
                "total_count": 1,
                "message": f"Found {len(sections_data)} sections for {course.code}"
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching sections: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def request_course_addition(
    student_id: str,
    course_code: str,
    section_code: str,
    reason: str | None = None,
) -> dict:
    """Request to add a specific course section with intelligent conflict handling.

    This tool provides a better user experience by:
    1. Checking the requested section first
    2. If conflicts exist, explaining them clearly
    3. Offering alternatives with justification
    4. Allowing user to proceed with their choice or accept alternatives

    Args:
        student_id: UUID string of the student
        course_code: Course code (e.g., "ENGR201")
        section_code: Section code (e.g., "B1")
        reason: Optional reason for the request
    """
    try:
        db = SessionLocal()

        # Find the requested section
        requested_section = (
            db.query(Section)
            .join(Course, Section.course_id == Course.course_id)
            .filter(
                Course.code == course_code,
                Section.section_code == section_code
            )
            .first()
        )

        if not requested_section:
            return {
                "success": False,
                "error": f"Section {course_code} {section_code} not found",
                "data": None,
            }

        # Check if the requested section is attachable
        eligibility_check = check_attachable(student_id, str(requested_section.section_id))

        if not eligibility_check["success"]:
            return {
                "success": False,
                "error": f"Eligibility check failed: {eligibility_check['error']}",
                "data": None,
            }

        # If no conflicts, check if we can auto-enroll or need advisor approval
        if eligibility_check.get("attachable", False):
            violations = eligibility_check.get("violations", [])

            # Check if any warnings require advisor approval
            needs_advisor_approval = any(
                v.get("severity") == "warning" and "advisor approval required" in v.get("message", "")
                for v in violations
            )

            if needs_advisor_approval:
                # Escalate to advisor due to academic standing or other warnings
                request_result = create_registration_request(
                    student_id=student_id,
                    request_type="ADD",
                    to_section_id=str(requested_section.section_id),
                    reason=reason or f"Student requested to add {course_code} {section_code}. Requires advisor approval due to academic standing."
                )

                if request_result["success"]:
                    return {
                        "success": True,
                        "preferred_card_types": ["request_summary", "week_grid", "generic"],
                        "data": {
                            **request_result["data"],
                            "message": f"📋 Your request to add {course_code} section {section_code} has been submitted for advisor review due to academic standing. Request ID: {request_result['data']['request_id']}",
                            "escalation_reason": "Academic standing requires advisor approval"
                        }
                    }
                else:
                    return request_result
            else:
                # All conditions met: seats available, no conflicts, prerequisites cleared, good standing
                # Proceed with automatic enrollment
                enrollment_result = create_automatic_enrollment(
                    student_id=student_id,
                    section_id=str(requested_section.section_id),
                    reason=reason or f"Automatic enrollment for {course_code} {section_code}"
                )

                if enrollment_result["success"]:
                    # Get updated schedule after successful enrollment
                    updated_schedule = get_current_schedule(student_id)
                    
                    return {
                        "success": True,
                        "preferred_card_types": ["week_grid", "course_info", "generic"],
                        "data": {
                            **enrollment_result,
                            "auto_enrolled": True,
                            "message": f"🎉 {enrollment_result['message']} All requirements met - no advisor approval needed.",
                            # Include updated schedule data for week_grid card
                            **(updated_schedule.get("data", {}) if updated_schedule.get("success") else {})
                        }
                    }
                else:
                    # Fallback to registration request if auto-enrollment fails
                    request_result = create_registration_request(
                        student_id=student_id,
                        request_type="ADD",
                        to_section_id=str(requested_section.section_id),
                        reason=f"Auto-enrollment failed, creating request: {enrollment_result.get('error', 'Unknown error')}"
                    )

                    return {
                        "success": True,
                        "preferred_card_types": ["request_summary", "week_grid", "generic"],
                        "data": {
                            **request_result.get("data", {}),
                            "message": f"⚠️ Auto-enrollment failed, created registration request instead. Request ID: {request_result.get('data', {}).get('request_id', 'N/A')}"
                        }
                    }

        # Handle conflicts - explain the issue and offer alternatives
        violations = eligibility_check.get("violations", [])
        suggested_alternatives = eligibility_check.get("suggested_alternatives", [])

        conflict_messages = []
        for violation in violations:
            if violation.get("severity") == "error" and "conflict" in violation.get("message", "").lower():
                conflict_messages.append(violation["message"])

        conflict_explanation = f"⚠️ Cannot add {course_code} section {section_code}: " + "; ".join(conflict_messages)

        # If we have alternatives, suggest the best one and try automatic enrollment
        if suggested_alternatives:
            best_alternative = suggested_alternatives[0]  # First alternative is typically the best

            # Check if alternative can be auto-enrolled
            alt_eligibility_check = check_attachable(student_id, best_alternative["section_id"])

            if alt_eligibility_check.get("attachable", False):
                alt_violations = alt_eligibility_check.get("violations", [])
                alt_needs_advisor = any(
                    v.get("severity") == "warning" and "advisor approval required" in v.get("message", "")
                    for v in alt_violations
                )

                if not alt_needs_advisor:
                    # Try automatic enrollment for alternative
                    enrollment_result = create_automatic_enrollment(
                        student_id=student_id,
                        section_id=best_alternative["section_id"],
                        reason=f"Automatic enrollment for alternative section {best_alternative['section_code']} due to conflict with {section_code}"
                    )

                    if enrollment_result["success"]:
                        # Get updated schedule after successful alternative enrollment
                        updated_schedule = get_current_schedule(student_id)
                        
                        return {
                            "success": True,
                            "preferred_card_types": ["alternatives", "week_grid", "generic"],
                            "data": {
                                "conflict_detected": True,
                                "requested_section": f"{course_code} {section_code}",
                                "alternative_used": f"{course_code} {best_alternative['section_code']}",
                                "conflict_reason": conflict_explanation,
                                "auto_enrolled": True,
                                "resolution_message": f"🔄 {conflict_explanation}\n\n🎉 I've automatically enrolled you in {course_code} section {best_alternative['section_code']} instead, which has no conflicts!",
                                "enrollment_details": enrollment_result,
                                "alternatives": suggested_alternatives,
                                "violations": violations,
                                # Include updated schedule data for week_grid card
                                **(updated_schedule.get("data", {}) if updated_schedule.get("success") else {})
                            }
                        }

            # Fallback to registration request if auto-enrollment not possible
            alternative_request = create_registration_request(
                student_id=student_id,
                request_type="ADD",
                to_section_id=best_alternative["section_id"],
                reason=f"Student requested {course_code} {section_code} but had time conflict. Switched to alternative section {best_alternative['section_code']} (requires advisor approval)."
            )

            if alternative_request["success"]:
                return {
                    "success": True,
                    "preferred_card_types": ["alternatives", "request_summary", "week_grid"],
                    "data": {
                        "conflict_detected": True,
                        "requested_section": f"{course_code} {section_code}",
                        "alternative_used": f"{course_code} {best_alternative['section_code']}",
                        "conflict_reason": conflict_explanation,
                        "resolution_message": f"🔄 {conflict_explanation}\n\n📋 I've submitted a request for {course_code} section {best_alternative['section_code']} instead (requires advisor approval).",
                        "request_details": alternative_request["data"],
                        "alternatives": suggested_alternatives,
                        "violations": violations
                    }
                }
            else:
                return {
                    "success": False,
                    "preferred_card_types": ["alternatives", "course_info"],
                    "error": f"{conflict_explanation} Alternative registration also failed: {alternative_request.get('error', 'Unknown error')}",
                    "data": {
                        "conflict_detected": True,
                        "requested_section": f"{course_code} {section_code}",
                        "conflict_reason": conflict_explanation,
                        "alternatives": suggested_alternatives,
                        "violations": violations
                    }
                }
        else:
            # No alternatives available
            return {
                "success": False,
                "preferred_card_types": ["course_info", "generic"],
                "error": f"{conflict_explanation} No alternative sections available.",
                "data": {
                    "conflict_detected": True,
                    "requested_section": f"{course_code} {section_code}",
                    "conflict_reason": conflict_explanation,
                    "violations": violations
                }
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing course addition request: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def create_registration_request(
    student_id: str,
    request_type: str,
    to_section_id: str | None = None,
    from_section_id: str | None = None,
    reason: str | None = None,
) -> dict:
    """Create a registration request for a student.

    Args:
        student_id: UUID string of the student
        request_type: Type of request - "ADD", "DROP", or "CHANGE_SECTION"
        to_section_id: Optional UUID string of section to add/change to
        from_section_id: Optional UUID string of section to drop/change from
        reason: Optional reason for the request
    """
    try:
        db = SessionLocal()

        # Validate student exists
        student = (
            db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        )
        if not student:
            return {"success": False, "error": "Student not found", "data": None}

        # Validate sections exist if provided
        if to_section_id:
            to_section = (
                db.query(Section)
                .filter(Section.section_id == UUID(to_section_id))
                .first()
            )
            if not to_section:
                return {
                    "success": False,
                    "error": "Target section not found",
                    "data": None,
                }

        if from_section_id:
            from_section = (
                db.query(Section)
                .filter(Section.section_id == UUID(from_section_id))
                .first()
            )
            if not from_section:
                return {
                    "success": False,
                    "error": "Source section not found",
                    "data": None,
                }

        # Check eligibility BEFORE creating the request (for ADD and CHANGE_SECTION types)
        if request_type in ["ADD", "CHANGE_SECTION"] and to_section_id:
            eligibility_check = check_attachable(student_id, to_section_id)

            if not eligibility_check["success"]:
                return {
                    "success": False,
                    "error": f"Eligibility check failed: {eligibility_check['error']}",
                    "data": None,
                }

            if not eligibility_check.get("attachable", False):
                violations = eligibility_check.get("violations", [])
                violation_messages = [v.get("message", "Unknown violation") for v in violations if v.get("severity") == "error"]

                return {
                    "success": False,
                    "preferred_card_types": ["alternatives", "course_info", "generic"],
                    "error": f"Cannot create registration request: {'; '.join(violation_messages)}",
                    "violations": violations,
                    "data": eligibility_check.get("data", {}),
                }

        # Create the registration request
        registration_request = RegistrationRequest(
            student_id=UUID(student_id),
            type=request_type,
            to_section_id=UUID(to_section_id) if to_section_id else None,
            from_section_id=UUID(from_section_id) if from_section_id else None,
            reason=reason,
            state="submitted",
            created_at=datetime.utcnow(),
        )

        db.add(registration_request)
        db.commit()
        db.refresh(registration_request)

        return {
            "success": True,
            "preferred_card_types": ["request_summary", "generic"],
            "data": {
                "request_id": str(registration_request.request_id),
                "type": registration_request.type,
                "state": registration_request.state,
                "reason": registration_request.reason,
                "created_at": registration_request.created_at.isoformat(),
                "message": f"Registration request created successfully. Request ID: {registration_request.request_id}",
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error creating registration request: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_current_schedule(student_id: str, term_id: str | None = None) -> dict:
    """Get the current enrolled schedule for a student, including pending requests.

    Args:
        student_id: UUID string of the student
        term_id: Optional term UUID to filter by
    """
    try:
        db = SessionLocal()

        # Get confirmed enrollments
        enrollment_query = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .join(Course, Section.course_id == Course.course_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered",
            )
        )

        if term_id:
            enrollment_query = enrollment_query.filter(Section.term_id == UUID(term_id))

        enrollments = enrollment_query.all()

        # Get pending registration requests
        pending_query = (
            db.query(RegistrationRequest)
            .join(Section, RegistrationRequest.to_section_id == Section.section_id)
            .join(Course, Section.course_id == Course.course_id)
            .filter(
                RegistrationRequest.student_id == UUID(student_id),
                RegistrationRequest.type == "ADD",
                RegistrationRequest.state == "submitted"
            )
        )

        if term_id:
            pending_query = pending_query.filter(Section.term_id == UUID(term_id))

        pending_requests = pending_query.all()

        schedule_data = []
        total_credits = 0
        pending_credits = 0

        # Process confirmed enrollments
        for enrollment in enrollments:
            section = enrollment.section
            course = section.course

            # Get meetings for this section
            meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == section.section_id)
                .all()
            )

            meetings_data = []
            for meeting in meetings:
                # Extract start and end times from PostgreSQL TSRANGE
                start_time = None
                end_time = None

                if meeting.time_range:
                    # PostgreSQL TSRANGE format: '[09:00:00,10:30:00)'
                    # Parse the time range to extract start and end times
                    time_str = str(meeting.time_range)
                    if '[' in time_str and ')' in time_str:
                        # Remove brackets and split by comma
                        time_part = time_str.strip('[]()').split(',')
                        if len(time_part) == 2:
                            start_time = time_part[0].strip()
                            end_time = time_part[1].strip()

                meetings_data.append(
                    {
                        "day_of_week": meeting.day_of_week,
                        "activity": meeting.activity,
                        "room": meeting.room.name if meeting.room else None,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                )

            schedule_data.append(
                {
                    "enrollment_id": str(enrollment.enrollment_id),
                    "course_code": course.code,
                    "course_title": course.title,
                    "credits": course.credits,
                    "section_code": section.section_code,
                    "instructor": section.instructor.name
                    if section.instructor
                    else "TBD",
                    "meetings": meetings_data,
                    "enrolled_at": enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at
                    else None,
                    "status": "enrolled"  # Mark as confirmed enrollment
                }
            )

            total_credits += course.credits

        # Process pending registration requests
        for request in pending_requests:
            section = request.to_section
            course = section.course

            # Get meetings for this section
            meetings = (
                db.query(SectionMeeting)
                .filter(SectionMeeting.section_id == section.section_id)
                .all()
            )

            meetings_data = []
            for meeting in meetings:
                # Extract start and end times from PostgreSQL TSRANGE
                start_time = None
                end_time = None

                if meeting.time_range:
                    # PostgreSQL TSRANGE format: '[09:00:00,10:30:00)'
                    # Parse the time range to extract start and end times
                    time_str = str(meeting.time_range)
                    if '[' in time_str and ')' in time_str:
                        # Remove brackets and split by comma
                        time_part = time_str.strip('[]()').split(',')
                        if len(time_part) == 2:
                            start_time = time_part[0].strip()
                            end_time = time_part[1].strip()

                meetings_data.append(
                    {
                        "day_of_week": meeting.day_of_week,
                        "activity": meeting.activity,
                        "room": meeting.room.name if meeting.room else None,
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                )

            schedule_data.append(
                {
                    "request_id": str(request.request_id),
                    "course_code": course.code,
                    "course_title": course.title,
                    "credits": course.credits,
                    "section_code": section.section_code,
                    "instructor": section.instructor.name
                    if section.instructor
                    else "TBD",
                    "meetings": meetings_data,
                    "requested_at": request.created_at.isoformat()
                    if request.created_at
                    else None,
                    "status": "pending"  # Mark as pending request
                }
            )

            pending_credits += course.credits

        return {
            "success": True,
            "preferred_card_types": ["week_grid", "schedule_diff", "generic"],
            "data": {
                "student_id": student_id,
                "term_id": term_id,
                "total_credits": total_credits,
                "pending_credits": pending_credits,
                "course_count": len(enrollments),
                "pending_count": len(pending_requests),
                "schedule": schedule_data,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting current schedule: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


# Placeholder tools for the complete SmolAgents architecture


def propose_alternatives(
    student_id: str, course_code: str, preferences: dict = None
) -> dict:
    """Propose alternative sections for a course based on student preferences.

    Args:
        student_id: UUID string of the student
        course_code: Course code to find alternatives for
        preferences: Optional dict with time/instructor preferences
    """
    # This would integrate with the optimization engine
    return {
        "success": True,
        "data": {
            "alternatives": [],
            "message": "Alternative section proposal feature coming soon",
        },
    }


def optimize_schedule(
    student_id: str, target_courses: list, preferences: dict = None
) -> dict:
    """Optimize a complete schedule for target courses.

    Args:
        student_id: UUID string of the student
        target_courses: List of course codes to include
        preferences: Optional dict with scheduling preferences
    """
    # This would integrate with the optimization engine
    return {
        "success": True,
        "data": {
            "proposal": {},
            "message": "Schedule optimization feature coming soon",
        },
    }


def build_schedule_diff(current_schedule: dict, proposed_changes: dict) -> dict:
    """Build a schedule diff card showing current vs proposed changes.

    Args:
        current_schedule: Current schedule data
        proposed_changes: Proposed adds/drops/changes
    """
    # This would build the UI card format
    return {
        "type": "schedule_diff",
        "payload": {
            "adds": proposed_changes.get("adds", []),
            "drops": proposed_changes.get("drops", []),
            "conflicts": [],
            "score_delta": 0.0,
        },
    }
