"""Advisor business logic tools for reviewing requests and managing approvals."""

from datetime import datetime
from typing import Any
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import (
    Course,
    Enrollment,
    RegistrationRequest,
    Section,
    Student,
)


class PendingRequestsResult(BaseModel):
    """Result structure for pending requests query."""
    success: bool = Field(description="Whether the operation was successful")
    requests: list[dict[str, Any]] = Field(description="List of pending requests")
    total_count: int = Field(description="Total number of pending requests")
    error: str | None = Field(description="Error message if operation failed")


class RuleExplanationResult(BaseModel):
    """Result structure for rule explanation."""
    success: bool = Field(description="Whether the rule was found and explained")
    rule_code: str = Field(description="The rule code that was explained")
    explanation: str = Field(description="Detailed explanation of the rule")
    examples: list[str] = Field(description="Examples of rule application")
    error: str | None = Field(description="Error message if operation failed")


class AlternativesResult(BaseModel):
    """Result structure for course alternatives proposal."""
    success: bool = Field(description="Whether alternatives were found")
    student_id: str = Field(description="Student ID for whom alternatives were proposed")
    original_course: str = Field(description="Original requested course")
    alternatives: list[dict[str, Any]] = Field(description="List of alternative courses")
    reasoning: str = Field(description="Explanation of why these alternatives were suggested")
    error: str | None = Field(description="Error message if operation failed")


class RequestDecisionResult(BaseModel):
    """Result structure for request decision."""
    success: bool = Field(description="Whether the decision was processed")
    request_id: str = Field(description="Request ID that was decided upon")
    decision: str = Field(description="The decision made (approved, denied, etc.)")
    reasoning: str = Field(description="Explanation for the decision")
    next_steps: str = Field(description="What happens next")
    error: str | None = Field(description="Error message if operation failed")


class StudentProfileResult(BaseModel):
    """Result structure for student profile."""
    success: bool = Field(description="Whether the profile was retrieved")
    student_info: dict[str, Any] = Field(description="Basic student information")
    academic_record: dict[str, Any] = Field(description="Academic history and performance")
    current_enrollment: list[dict[str, Any]] = Field(description="Current course enrollments")
    requirements_status: dict[str, Any] = Field(description="Degree requirements progress")
    error: str | None = Field(description="Error message if operation failed")


class AdviseesResult(BaseModel):
    """Result structure for advisees list."""
    success: bool = Field(description="Whether the advisees list was retrieved")
    advisees: list[dict[str, Any]] = Field(description="List of students advised by this advisor")
    total_count: int = Field(description="Total number of advisees")
    active_requests: int = Field(description="Number of advisees with pending requests")
    error: str | None = Field(description="Error message if operation failed")


@tool
def get_pending_requests(advisor_id: str, program_code: str | None = None) -> PendingRequestsResult:
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

        request_list = []
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

            request_list.append(request_data)

        db.close()

        return PendingRequestsResult(
            success=True,
            requests=request_list,
            total_count=len(request_list),
            error=None
        )

    except Exception as e:
        return PendingRequestsResult(
            success=False,
            requests=[],
            total_count=0,
            error=f"Error getting pending requests: {str(e)}"
        )


@tool
def explain_rule(rule_code: str) -> RuleExplanationResult:
    """Explain a specific business rule and its rationale.

    Args:
        rule_code: Business rule code (e.g., "BR-001", "BR-002")
    """
    rules = {
        "BR-001": {
            "title": "Academic Standing Restriction",
            "description": "Students on academic probation or suspension require advisor approval for course changes",
            "rationale": "Ensures academic oversight for at-risk students",
            "examples": [
                "Student on probation needs advisor approval to drop a course",
                "Student on suspension requires approval to add courses"
            ]
        },
        "BR-002": {
            "title": "Section Capacity Limit",
            "description": "Cannot enroll in sections at or above capacity",
            "rationale": "Maintains classroom management and resource allocation",
            "examples": [
                "CS101 section A1 has 30/30 students enrolled",
                "Department head can override capacity limits"
            ]
        },
        "BR-003": {
            "title": "Prerequisite Requirement",
            "description": "Must complete required prerequisites before enrollment",
            "rationale": "Ensures academic preparation and success",
            "examples": [
                "CS101 required before CS201",
                "MATH120 with C+ grade required for MATH220"
            ]
        },
        "BR-005": {
            "title": "Schedule Time Conflict",
            "description": "Cannot enroll in courses with overlapping meeting times",
            "rationale": "Physical attendance requirements",
            "examples": [
                "CS101 MWF 9:00-10:00 conflicts with MATH120 MWF 9:30-10:30",
                "Lab sections cannot overlap with lecture sections"
            ]
        },
    }

    rule_info = rules.get(rule_code)
    
    if rule_info:
        return RuleExplanationResult(
            success=True,
            rule_code=rule_code,
            explanation=f"{rule_info['title']}: {rule_info['description']}. {rule_info['rationale']}",
            examples=rule_info["examples"],
            error=None
        )
    else:
        return RuleExplanationResult(
            success=False,
            rule_code=rule_code,
            explanation="",
            examples=[],
            error=f"Rule code '{rule_code}' not found in rule database"
        )


@tool
def propose_alternatives(student_id: str, original_request: dict) -> AlternativesResult:
    """Propose alternative sections or courses for a problematic request.

    Args:
        student_id: UUID string of the student
        original_request: Original request data that has violations
    """
    try:
        db = SessionLocal()

        # Get student info
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            db.close()
            return AlternativesResult(
                success=False,
                student_id=student_id,
                original_course="",
                alternatives=[],
                reasoning="",
                error="Student not found"
            )

        # Extract original course info
        original_course = original_request.get("course_code", "")
        
        # This would implement sophisticated alternative finding logic
        alternatives = [
            {
                "option": 1,
                "description": "Different section with no time conflicts",
                "course_code": "CS101",
                "section_code": "B1",
                "time": "TTh 2:00-3:30 PM",
                "instructor": "Dr. Smith",
                "capacity_available": 5,
                "conflicts": [],
                "viability_score": 0.9,
            },
            {
                "option": 2,
                "description": "Alternative course meeting similar requirements",
                "course_code": "CS102",
                "section_code": "A1",
                "time": "MWF 10:00-11:00 AM",
                "instructor": "Prof. Johnson",
                "capacity_available": 3,
                "conflicts": [],
                "viability_score": 0.7,
            },
        ]

        reasoning = "Option 1 provides the best fit with minimal schedule disruption. Option 2 offers similar learning outcomes but different focus area."

        db.close()

        return AlternativesResult(
            success=True,
            student_id=student_id,
            original_course=original_course,
            alternatives=alternatives,
            reasoning=reasoning,
            error=None
        )

    except Exception as e:
        return AlternativesResult(
            success=False,
            student_id=student_id,
            original_course="",
            alternatives=[],
            reasoning="",
            error=f"Error proposing alternatives: {str(e)}"
        )


@tool
def decide_request(
    request_id: str, action: str, rationale: str, advisor_id: str
) -> RequestDecisionResult:
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
            db.close()
            return RequestDecisionResult(
                success=False,
                request_id=request_id,
                decision="",
                reasoning="",
                next_steps="",
                error="Request not found"
            )

        # Update request state based on action
        state_mapping = {
            "approve": "advisor_approved",
            "reject": "rejected",
            "refer": "referred",
            "hold": "on_hold",
        }

        new_state = state_mapping.get(action)
        if not new_state:
            db.close()
            return RequestDecisionResult(
                success=False,
                request_id=request_id,
                decision="",
                reasoning="",
                next_steps="",
                error=f"Invalid action: {action}"
            )

        request.state = new_state
        request.advisor_notes = rationale
        request.reviewed_at = datetime.utcnow()

        db.commit()
        db.close()

        # Determine next steps based on action
        next_steps_mapping = {
            "approve": "Request approved and will proceed to enrollment processing",
            "reject": "Request rejected. Student will be notified and can appeal or submit new request",
            "refer": "Request referred to department head for final decision",
            "hold": "Request placed on hold pending additional information"
        }

        return RequestDecisionResult(
            success=True,
            request_id=request_id,
            decision=action,
            reasoning=rationale,
            next_steps=next_steps_mapping[action],
            error=None
        )

    except Exception as e:
        return RequestDecisionResult(
            success=False,
            request_id=request_id,
            decision="",
            reasoning="",
            next_steps="",
            error=f"Error deciding request: {str(e)}"
        )


@tool
def get_student_profile(student_id: str, advisor_id: str) -> StudentProfileResult:
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
            db.close()
            return StudentProfileResult(
                success=False,
                student_info={},
                academic_record={},
                current_enrollment=[],
                requirements_status={},
                error="Student not found"
            )

        # Basic student information
        student_info = {
            "student_id": str(student.student_id),
            "external_sis_id": student.external_sis_id,
            "gpa": float(student.gpa) if student.gpa else None,
            "credits_completed": student.credits_completed,
            "standing": student.standing,
            "status": student.student_status,
        }

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

        current_enrollment = [
            {
                "course_code": enrollment.section.course.code,
                "course_title": enrollment.section.course.title,
                "section_code": enrollment.section.section_code,
                "credits": enrollment.section.course.credits,
                "instructor": enrollment.section.instructor or "TBA",
                "schedule": enrollment.section.schedule or "TBA"
            }
            for enrollment in enrollments
        ]

        # Get recent requests
        recent_requests = (
            db.query(RegistrationRequest)
            .filter(RegistrationRequest.student_id == UUID(student_id))
            .order_by(RegistrationRequest.created_at.desc())
            .limit(10)
            .all()
        )

        academic_record = {
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
            "total_requests": len(recent_requests)
        }

        # Mock requirements status (would calculate from actual requirements)
        requirements_status = {
            "credits_toward_degree": student.credits_completed or 0,
            "credits_remaining": max(0, 120 - (student.credits_completed or 0)),
            "major_requirements_met": "75%",
            "general_education_met": "90%"
        }

        db.close()

        return StudentProfileResult(
            success=True,
            student_info=student_info,
            academic_record=academic_record,
            current_enrollment=current_enrollment,
            requirements_status=requirements_status,
            error=None
        )

    except Exception as e:
        return StudentProfileResult(
            success=False,
            student_info={},
            academic_record={},
            current_enrollment=[],
            requirements_status={},
            error=f"Error getting student profile: {str(e)}"
        )


@tool
def get_advisees(advisor_id: str) -> AdviseesResult:
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

        active_requests = sum(advisee["pending_requests"] for advisee in advisees)

        db.close()

        return AdviseesResult(
            success=True,
            advisees=advisees,
            total_count=len(advisees),
            active_requests=active_requests,
            error=None
        )

    except Exception as e:
        return AdviseesResult(
            success=False,
            advisees=[],
            total_count=0,
            active_requests=0,
            error=f"Error getting advisees: {str(e)}"
        )


# Helper functions for business logic

def _check_advisor_authorization(advisor_id: str, student_id: str) -> bool:
    """Check if advisor is authorized to access student information."""
    # Would implement proper authorization logic
    return True


def _calculate_requirements_progress(student: Student) -> dict:
    """Calculate student's progress toward degree requirements."""
    # Would implement actual requirements calculation
    return {
        "major_requirements": "75%",
        "general_education": "90%",
        "total_credits": student.credits_completed or 0,
        "credits_remaining": max(0, 120 - (student.credits_completed or 0))
    }


def _find_alternative_sections(course_code: str, student_schedule: list) -> list[dict]:
    """Find alternative sections that don't conflict with student's schedule."""
    # Would implement sophisticated scheduling logic
    return []


def _validate_request_decision(request: RegistrationRequest, action: str) -> str | None:
    """Validate that a decision is appropriate for the given request."""
    valid_actions = ["approve", "reject", "refer", "hold"]
    
    if action not in valid_actions:
        return f"Invalid action. Must be one of: {', '.join(valid_actions)}"
    
    # Additional validation logic would go here
    return None
