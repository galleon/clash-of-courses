"""Advisor agent tools for reviewing requests and managing approvals."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from smolagents import tool

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import (
    Course,
    Enrollment,
    RegistrationRequest,
    Section,
    Student,
    User,
)


@tool
def get_pending_requests(advisor_id: str, program_code: str | None = None) -> dict:
    """Get pending registration requests for review by advisor.

    Args:
        advisor_id: UUID string of the advisor
        program_code: Optional program code to filter by
    """
    try:
        db = SessionLocal()

        # Get pending requests (simplified - would include proper advisor scoping)
        query = (
            db.query(RegistrationRequest)
            .join(Student, RegistrationRequest.student_id == Student.student_id)
            .filter(RegistrationRequest.state.in_(["submitted", "pending_approval"]))
        )

        if program_code:
            # Would filter by student's program
            pass

        requests = query.all()

        requests_data = []
        for request in requests:
            student = request.student
            to_section = None
            from_section = None

            if request.to_section_id:
                to_section = (
                    db.query(Section)
                    .filter(Section.section_id == request.to_section_id)
                    .first()
                )

            if request.from_section_id:
                from_section = (
                    db.query(Section)
                    .filter(Section.section_id == request.from_section_id)
                    .first()
                )

            request_data = {
                "request_id": str(request.request_id),
                "type": request.type,
                "state": request.state,
                "reason": request.reason,
                "created_at": request.created_at.isoformat(),
                "student": {
                    "student_id": str(student.student_id),
                    "external_sis_id": student.external_sis_id,
                    "gpa": float(student.gpa) if student.gpa else None,
                    "standing": student.standing,
                },
                "to_section": {
                    "section_id": str(to_section.section_id),
                    "course_code": to_section.course.code,
                    "course_title": to_section.course.title,
                    "section_code": to_section.section_code,
                }
                if to_section
                else None,
                "from_section": {
                    "section_id": str(from_section.section_id),
                    "course_code": from_section.course.code,
                    "course_title": from_section.course.title,
                    "section_code": from_section.section_code,
                }
                if from_section
                else None,
            }

            requests_data.append(request_data)

        return {
            "success": True,
            "data": {"count": len(requests), "requests": requests_data},
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting pending requests: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def explain_rule(rule_code: str) -> dict:
    """Explain a specific business rule and its rationale.

    Args:
        rule_code: Business rule code (e.g., "BR-001", "BR-002")
    """
    rules = {
        "BR-001": {
            "title": "Academic Standing Restriction",
            "description": "Students on academic probation or suspension require advisor approval for course changes",
            "rationale": "Ensures academic oversight for at-risk students",
            "severity": "warning",
            "approval_required": "advisor",
        },
        "BR-002": {
            "title": "Section Capacity Limit",
            "description": "Cannot enroll in sections at or above capacity",
            "rationale": "Maintains classroom management and resource allocation",
            "severity": "error",
            "approval_required": "department_head",
        },
        "BR-003": {
            "title": "Prerequisite Requirement",
            "description": "Must complete required prerequisites before enrollment",
            "rationale": "Ensures academic preparation and success",
            "severity": "error",
            "approval_required": "department_head",
        },
        "BR-005": {
            "title": "Schedule Time Conflict",
            "description": "Cannot enroll in courses with overlapping meeting times",
            "rationale": "Physical attendance requirements",
            "severity": "error",
            "approval_required": "advisor",
        },
    }

    if rule_code in rules:
        return {"success": True, "data": rules[rule_code]}
    else:
        return {
            "success": False,
            "error": f"Rule code {rule_code} not found",
            "data": None,
        }


@tool
def propose_alternatives(student_id: str, original_request: dict) -> dict:
    """Propose alternative sections or courses for a problematic request.

    Args:
        student_id: UUID string of the student
        original_request: Original request data that has violations
    """
    try:
        db = SessionLocal()

        # This would implement sophisticated alternative finding logic
        # For now, return a mock response
        alternatives = [
            {
                "option": 1,
                "description": "Different section with no time conflicts",
                "sections": [
                    {
                        "section_id": "mock-section-1",
                        "course_code": "CS101",
                        "section_code": "B1",
                        "time": "TTh 2:00-3:30 PM",
                        "conflicts": [],
                        "capacity_available": 5,
                    }
                ],
                "viability_score": 0.9,
            },
            {
                "option": 2,
                "description": "Alternative course meeting similar requirements",
                "sections": [
                    {
                        "section_id": "mock-section-2",
                        "course_code": "CS102",
                        "section_code": "A1",
                        "time": "MWF 10:00-11:00 AM",
                        "conflicts": [],
                        "capacity_available": 3,
                    }
                ],
                "viability_score": 0.7,
            },
        ]

        return {
            "success": True,
            "data": {
                "alternatives": alternatives,
                "recommendation": "Option 1 provides the best fit with minimal schedule disruption",
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error proposing alternatives: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def decide_request(
    request_id: str, action: str, rationale: str, advisor_id: str
) -> dict:
    """Make a decision on a registration request.

    Args:
        request_id: UUID string of the request
        action: Decision action - "approve", "reject", "refer", "hold"
        rationale: Explanation for the decision
        advisor_id: UUID string of the advisor making the decision
    """
    try:
        db = SessionLocal()

        request = (
            db.query(RegistrationRequest)
            .filter(RegistrationRequest.request_id == UUID(request_id))
            .first()
        )

        if not request:
            return {"success": False, "error": "Request not found", "data": None}

        # Update request state based on action
        state_mapping = {
            "approve": "advisor_approved",
            "reject": "rejected",
            "refer": "referred",
            "hold": "on_hold",
        }

        request.state = state_mapping.get(action, "unknown")
        request.advisor_notes = rationale
        request.reviewed_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "data": {
                "request_id": request_id,
                "action": action,
                "state": request.state,
                "rationale": rationale,
                "message": f"Request {action}ed successfully",
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error deciding request: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_student_profile(student_id: str, advisor_id: str) -> dict:
    """Get comprehensive student profile for advisor review.

    Args:
        student_id: UUID string of the student
        advisor_id: UUID string of the advisor (for authorization)
    """
    try:
        db = SessionLocal()

        student = (
            db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        )
        if not student:
            return {"success": False, "error": "Student not found", "data": None}

        # Get current enrollments
        enrollments = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .join(Course, Section.course_id == Course.course_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered",
            )
            .all()
        )

        # Get recent requests
        recent_requests = (
            db.query(RegistrationRequest)
            .filter(RegistrationRequest.student_id == UUID(student_id))
            .order_by(RegistrationRequest.created_at.desc())
            .limit(10)
            .all()
        )

        profile_data = {
            "student": {
                "student_id": str(student.student_id),
                "external_sis_id": student.external_sis_id,
                "gpa": float(student.gpa) if student.gpa else None,
                "credits_completed": student.credits_completed,
                "standing": student.standing,
                "status": student.student_status,
            },
            "current_enrollments": [
                {
                    "course_code": enrollment.section.course.code,
                    "course_title": enrollment.section.course.title,
                    "section_code": enrollment.section.section_code,
                    "credits": enrollment.section.course.credits,
                }
                for enrollment in enrollments
            ],
            "recent_requests": [
                {
                    "request_id": str(request.request_id),
                    "type": request.type,
                    "state": request.state,
                    "created_at": request.created_at.isoformat(),
                    "reason": request.reason,
                }
                for request in recent_requests
            ],
        }

        return {"success": True, "data": profile_data}

    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting student profile: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_advisees(advisor_id: str) -> dict:
    """Get list of students assigned to this advisor.

    Args:
        advisor_id: UUID string of the advisor
    """
    try:
        db = SessionLocal()

        # Mock implementation - would need proper advisor-student relationships
        advisees = [
            {
                "student_id": "student-1",
                "external_sis_id": "12345",
                "full_name": "Sarah Johnson",
                "program": "Computer Science",
                "year": "Junior",
                "gpa": 3.7,
                "standing": "good",
                "pending_requests": 2,
            },
            {
                "student_id": "student-2",
                "external_sis_id": "12346",
                "full_name": "Michael Chen",
                "program": "Computer Science",
                "year": "Senior",
                "gpa": 3.9,
                "standing": "good",
                "pending_requests": 0,
            },
        ]

        return {"success": True, "data": {"count": len(advisees), "advisees": advisees}}

    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting advisees: {str(e)}",
            "data": None,
        }
    finally:
        db.close()
