"""Student agent tools for course management."""

import datetime
from smolagents import tool

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import User, Course, Section, Request
from brs_backend.core.logging import log_detailed


@tool
def check_pending_requests(student_id: int) -> dict:
    """QUICK CHECK: Get only pending registration requests for a student.
    Use this for 'pending issues', 'pending requests', or similar queries.

    Args:
        student_id: The ID of the student to check
    """
    try:
        db = SessionLocal()

        # Get only pending requests
        pending_requests = (
            db.query(Request)
            .join(Course, Request.course_id == Course.id)
            .filter(Request.student_id == student_id, Request.status == "pending")
            .all()
        )

        if not pending_requests:
            return {
                "success": True,
                "data": {
                    "message": "You have no pending requests.",
                    "count": 0,
                    "requests": [],
                },
            }

        # Format pending requests
        requests_data = []
        for req in pending_requests:
            # Get course details with explicit query
            course = db.query(Course).filter(Course.id == req.course_id).first()
            requests_data.append(
                {
                    "request_id": req.id,
                    "course_code": course.code if course else None,
                    "course_name": course.name if course else None,
                    "justification": req.justification,
                    "request_date": req.created_at.isoformat()
                    if req.created_at
                    else None,
                    "status": req.status,
                }
            )

        return {
            "success": True,
            "data": {
                "message": f"You have {len(pending_requests)} pending request(s).",
                "count": len(pending_requests),
                "requests": requests_data,
            },
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
def get_current_enrollments(student_id: int) -> dict:
    """QUICK CHECK: Get only current enrolled courses for a student.
    Use this for 'what courses am I taking', 'my courses', or enrollment queries.

    Args:
        student_id: The ID of the student to check
    """
    try:
        db = SessionLocal()

        # Get approved enrollments
        enrolled_courses = (
            db.query(Request)
            .join(Course, Request.course_id == Course.id)
            .filter(
                Request.student_id == student_id,
                Request.status == "approved",
                Request.request_type == "add",
            )
            .all()
        )

        if not enrolled_courses:
            return {
                "success": True,
                "data": {
                    "message": "You are not currently enrolled in any courses.",
                    "count": 0,
                    "courses": [],
                },
            }

        # Format courses
        courses_data = []
        for enrollment in enrolled_courses:
            # Explicitly fetch course to ensure credits field is available
            course = db.query(Course).filter(Course.id == enrollment.course_id).first()
            courses_data.append(
                {
                    "course_code": course.code if course else "Unknown",
                    "course_name": course.name if course else "Unknown",
                    "description": course.description if course else None,
                    "credits": course.credits if course else None,
                }
            )

        return {
            "success": True,
            "data": {
                "message": f"You are enrolled in {len(enrolled_courses)} course(s).",
                "count": len(enrolled_courses),
                "courses": courses_data,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting enrollments: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_student_info(student_id: int) -> dict:
    """Get comprehensive information about a student including profile, enrolled courses, and pending requests.
    Use this for questions about pending requests, current enrollments, or student details.

    Args:
        student_id: The ID of the student to retrieve information for
    """
    try:
        db = SessionLocal()
        student = (
            db.query(User).filter(User.id == student_id, User.role == "student").first()
        )

        if not student:
            return {
                "success": False,
                "error": f"Student with ID {student_id} not found.",
                "data": None,
            }

        # Get student's enrolled courses (approved registration requests)
        enrolled_courses = (
            db.query(Request)
            .join(Course, Request.course_id == Course.id)
            .filter(
                Request.student_id == student_id,
                Request.status == "approved",
                Request.request_type == "add",
            )
            .all()
        )

        # Format enrolled courses data
        current_courses = []
        for enrollment in enrolled_courses:
            # Explicitly fetch course to ensure credits field is available
            course = db.query(Course).filter(Course.id == enrollment.course_id).first()
            course_info = {
                "course_id": course.id if course else None,
                "course_code": course.code if course else "Unknown",
                "course_name": course.name if course else "Unknown",
                "description": course.description if course else None,
                "registration_date": enrollment.created_at.isoformat()
                if enrollment.created_at
                else None,
                "section_id": enrollment.section_to_id
                if enrollment.section_to_id
                else None,
            }

            # Add section details if available
            if enrollment.section_to:
                course_info.update(
                    {
                        "section_code": enrollment.section_to.section_code,
                        "schedule": enrollment.section_to.schedule,
                        "instructor": enrollment.section_to.instructor,
                    }
                )

            current_courses.append(course_info)

        # Get student's pending requests
        pending_requests = (
            db.query(Request)
            .join(Course, Request.course_id == Course.id)
            .filter(
                Request.student_id == student_id,
                Request.status == "pending",
                Request.request_type == "add",
            )
            .all()
        )

        # Format pending requests data
        pending_course_requests = []
        for request in pending_requests:
            # Get course details with explicit query
            course = db.query(Course).filter(Course.id == request.course_id).first()
            request_info = {
                "request_id": request.id,
                "course_id": course.id if course else None,
                "course_code": course.code if course else None,
                "course_name": course.name if course else None,
                "description": course.description if course else None,
                "justification": request.justification,
                "request_date": request.created_at.isoformat()
                if request.created_at
                else None,
                "status": request.status,
            }
            pending_course_requests.append(request_info)

        result = {
            "success": True,
            "error": None,
            "data": {
                "id": student.id,
                "full_name": student.full_name,
                "major": student.major,
                "gpa": student.gpa,
                "credit_hours_completed": student.credit_hours_completed,
                "role": student.role,
                "enrolled_courses": current_courses,
                "total_enrolled_courses": len(current_courses),
                "pending_requests": pending_course_requests,
                "total_pending_requests": len(pending_course_requests),
            },
        }

        db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving student info: {str(e)}",
            "data": None,
        }


@tool
def find_course_by_code(course_code: str) -> dict:
    """QUICK LOOKUP: Find a course by its code and get basic information.
    Use this when user mentions a course code like 'CS101' to verify it exists.

    Args:
        course_code: The course code to look up (e.g., 'CS101')
    """
    try:
        db = SessionLocal()
        course = db.query(Course).filter(Course.code.ilike(f"%{course_code}%")).first()

        if not course:
            # Try exact match
            course = db.query(Course).filter(Course.code == course_code.upper()).first()

        if not course:
            return {
                "success": False,
                "error": f"Course '{course_code}' not found. Please check the course code or browse available courses.",
                "data": None,
            }

        return {
            "success": True,
            "data": {
                "course_id": course.id,
                "course_code": course.code,
                "course_name": course.name,
                "description": course.description,
                "message": f"Found course: {course.code} - {course.name}",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error finding course: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_available_courses() -> dict:
    """Get a list of all available courses with their details."""
    try:
        db = SessionLocal()
        courses = db.query(Course).all()

        course_data = []
        for course in courses:
            course_data.append(
                {
                    "id": course.id,
                    "code": course.code,
                    "name": course.name,
                    "description": getattr(course, "description", None),
                }
            )

        db.close()
        return {
            "success": True,
            "error": None,
            "data": {"courses": course_data, "total_count": len(course_data)},
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving courses: {str(e)}",
            "data": None,
        }


@tool
def check_course_sections(course_code: str) -> dict:
    """Check available sections for a specific course.

    Args:
        course_code: The course code to check sections for (e.g., 'CS101')
    """
    try:
        db = SessionLocal()
        course = db.query(Course).filter(Course.code == course_code).first()

        if not course:
            db.close()
            return {
                "success": False,
                "error": f"Course {course_code} not found.",
                "data": None,
            }

        sections = db.query(Section).filter(Section.course_id == course.id).all()

        if not sections:
            db.close()
            return {
                "success": True,
                "error": None,
                "data": {
                    "course_code": course_code,
                    "course_title": course.name,
                    "sections": [],
                    "message": f"No sections available for {course_code}.",
                },
            }

        section_data = []
        for section in sections:
            section_data.append(
                {
                    "id": section.id,
                    "section_number": section.section_code,
                    "schedule": section.schedule,
                    "instructor": section.instructor,
                    "max_students": getattr(section, "capacity", 0),
                    "current_enrollment": getattr(section, "seats_taken", 0),
                }
            )

        db.close()
        return {
            "success": True,
            "error": None,
            "data": {
                "course_code": course_code,
                "course_title": course.name,
                "sections": section_data,
                "total_sections": len(section_data),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving sections: {str(e)}",
            "data": None,
        }


@tool
def create_registration_request(
    student_id: int, course_code: str, justification: str
) -> dict:
    """Create a new registration request for a student.

    Args:
        student_id: The ID of the student making the request
        course_code: The course code to request (e.g., 'CS101')
        justification: The reason for the registration request
    """
    try:
        db = SessionLocal()

        # Find course
        course = db.query(Course).filter(Course.code == course_code).first()
        if not course:
            db.close()
            return {
                "success": False,
                "error": f"Course {course_code} not found.",
                "data": None,
            }

        # Check for existing request
        existing_request = (
            db.query(Request)
            .filter(
                Request.student_id == student_id,
                Request.course_id == course.id,
                Request.status.in_(["pending", "approved"]),
            )
            .first()
        )

        if existing_request:
            db.close()
            return {
                "success": False,
                "error": f"You already have a {existing_request.status} request for {course_code}.",
                "data": {
                    "existing_request_id": existing_request.id,
                    "existing_status": existing_request.status,
                    "course_code": course_code,
                },
            }

        # Create request
        new_request = Request(
            student_id=student_id,
            course_id=course.id,
            request_type="add",
            status="pending",
            justification=justification,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )

        db.add(new_request)
        db.commit()
        db.refresh(new_request)

        result = {
            "success": True,
            "error": None,
            "data": {
                "request_id": new_request.id,
                "student_id": student_id,
                "course_code": course_code,
                "course_title": course.name,
                "status": "pending",
                "justification": justification,
                "created_at": new_request.created_at.isoformat(),
                "message": "Registration request created successfully. Your request is pending advisor approval.",
            },
        }

        db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating request: {str(e)}",
            "data": None,
        }
