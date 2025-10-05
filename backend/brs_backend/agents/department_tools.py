"""Department head business logic tools for policy decisions and overrides."""

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


class DepartmentRequestsResult(BaseModel):
    """Result structure for department requests query."""
    success: bool = Field(description="Whether the operation was successful")
    requests: list[dict[str, Any]] = Field(description="List of department requests")
    total_count: int = Field(description="Total number of requests")
    pending_count: int = Field(description="Number of pending requests")
    error: str | None = Field(description="Error message if operation failed")


class CapacityOverrideResult(BaseModel):
    """Result structure for capacity override operation."""
    success: bool = Field(description="Whether the override was successful")
    section_id: str = Field(description="Section ID that was modified")
    old_capacity: int = Field(description="Previous capacity limit")
    new_capacity: int = Field(description="New capacity limit")
    justification: str = Field(description="Justification for the override")
    impact_analysis: str = Field(description="Analysis of the override impact")
    error: str | None = Field(description="Error message if operation failed")


class FinalApprovalResult(BaseModel):
    """Result structure for final request approval."""
    success: bool = Field(description="Whether the approval was processed")
    request_id: str = Field(description="Request ID that was approved or denied")
    decision: str = Field(description="Final decision made")
    reasoning: str = Field(description="Reasoning for the decision")
    next_steps: str = Field(description="What happens next")
    precedent_note: str = Field(description="Notes about policy precedent")
    error: str | None = Field(description="Error message if operation failed")


class EnrollmentAnalyticsResult(BaseModel):
    """Result structure for enrollment analytics."""
    success: bool = Field(description="Whether analytics were generated")
    department_id: str = Field(description="Department analyzed")
    term_id: str = Field(description="Term analyzed")
    enrollment_summary: dict[str, Any] = Field(description="Overall enrollment metrics")
    course_analytics: list[dict[str, Any]] = Field(description="Per-course analytics")
    trends: dict[str, Any] = Field(description="Enrollment trends and patterns")
    recommendations: list[str] = Field(description="Strategic recommendations")
    error: str | None = Field(description="Error message if operation failed")


class PolicyExceptionResult(BaseModel):
    """Result structure for policy exception management."""
    success: bool = Field(description="Whether the exception was processed")
    request_id: str = Field(description="Request requiring exception")
    exception_type: str = Field(description="Type of exception granted")
    decision: str = Field(description="Exception decision")
    justification: str = Field(description="Justification for exception")
    policy_impact: str = Field(description="Impact on departmental policies")
    documentation: str = Field(description="Required documentation")
    error: str | None = Field(description="Error message if operation failed")


class ScheduleViewResult(BaseModel):
    """Result structure for department schedule view."""
    success: bool = Field(description="Whether schedule was retrieved")
    department_id: str = Field(description="Department viewed")
    term_id: str = Field(description="Term viewed")
    courses: list[dict[str, Any]] = Field(description="Course schedule information")
    capacity_summary: dict[str, Any] = Field(description="Capacity utilization summary")
    resource_allocation: dict[str, Any] = Field(description="Resource allocation analysis")
    scheduling_conflicts: list[str] = Field(description="Identified scheduling issues")
    error: str | None = Field(description="Error message if operation failed")


@tool
def get_department_requests(
    department_id: str, status_filter: str | None = None
) -> DepartmentRequestsResult:
    """Get registration requests requiring department-level review.

    Args:
        department_id: UUID string of the department
        status_filter: Optional status to filter by (e.g., "pending_department")
    """
    try:
        db = SessionLocal()

        # Get requests requiring department approval
        query = (
            db.query(RegistrationRequest)
            .join(Student, RegistrationRequest.student_id == Student.student_id)
            .filter(
                RegistrationRequest.state.in_(
                    ["advisor_approved", "pending_department"]
                )
            )
        )

        if status_filter:
            query = query.filter(RegistrationRequest.state == status_filter)

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
                "advisor_notes": request.advisor_notes,
                "created_at": request.created_at.isoformat(),
                "reviewed_at": request.reviewed_at.isoformat()
                if request.reviewed_at
                else None,
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
                    "capacity": to_section.capacity,
                    "enrolled": db.query(Enrollment)
                    .filter(
                        Enrollment.section_id == to_section.section_id,
                        Enrollment.status == "registered",
                    )
                    .count(),
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

        pending_count = sum(1 for req in requests_data if req["state"] in ["pending_department", "referred"])

        db.close()

        return DepartmentRequestsResult(
            success=True,
            requests=requests_data,
            total_count=len(requests_data),
            pending_count=pending_count,
            error=None
        )

    except Exception as e:
        return DepartmentRequestsResult(
            success=False,
            requests=[],
            total_count=0,
            pending_count=0,
            error=f"Error getting department requests: {str(e)}"
        )


@tool
def override_capacity(
    section_id: str, new_capacity: int, department_head_id: str, justification: str
) -> dict:
    """Override section capacity limits for exceptional cases.

    Args:
        section_id: UUID string of the section
        new_capacity: New capacity limit
        department_head_id: UUID string of the department head
        justification: Justification for the override
    """
    try:
        db = SessionLocal()

        section = (
            db.query(Section).filter(Section.section_id == UUID(section_id)).first()
        )
        if not section:
            return {"success": False, "error": "Section not found", "data": None}

        original_capacity = section.capacity
        section.capacity = new_capacity

        # Log the override (in production, this would go to an audit table)
        override_log = {
            "section_id": section_id,
            "original_capacity": original_capacity,
            "new_capacity": new_capacity,
            "authorized_by": department_head_id,
            "justification": justification,
            "timestamp": datetime.utcnow().isoformat(),
        }

        db.commit()

        return {
            "success": True,
            "data": {
                "section_id": section_id,
                "course_code": section.course.code,
                "section_code": section.section_code,
                "original_capacity": original_capacity,
                "new_capacity": new_capacity,
                "override_log": override_log,
                "message": f"Capacity override successful: {original_capacity} → {new_capacity}",
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error overriding capacity: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def final_approve_request(
    request_id: str, department_head_id: str, notes: str = None
) -> dict:
    """Provide final approval for a registration request.

    Args:
        request_id: UUID string of the request
        department_head_id: UUID string of the department head
        notes: Optional additional notes
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

        request.state = "approved"
        request.department_notes = notes
        request.final_approved_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "data": {
                "request_id": request_id,
                "state": request.state,
                "approved_by": department_head_id,
                "notes": notes,
                "message": "Request approved successfully",
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error approving request: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def get_enrollment_analytics(department_id: str, term_id: str | None = None) -> EnrollmentAnalyticsResult:
    """Generate enrollment analytics for department courses.

    Args:
        department_id: UUID string of the department
        term_id: Optional term UUID to filter by
    """
    try:
        db = SessionLocal()

        # Mock analytics data - would calculate real metrics in production
        analytics = {
            "overview": {
                "total_sections": 45,
                "total_capacity": 1125,
                "total_enrolled": 987,
                "utilization_rate": 0.877,
                "waitlist_total": 23,
            },
            "by_course": [
                {
                    "course_code": "CS101",
                    "course_title": "Intro to Programming",
                    "sections": 3,
                    "capacity": 75,
                    "enrolled": 73,
                    "utilization": 0.973,
                    "waitlist": 5,
                },
                {
                    "course_code": "CS201",
                    "course_title": "Data Structures",
                    "sections": 2,
                    "capacity": 50,
                    "enrolled": 48,
                    "utilization": 0.96,
                    "waitlist": 2,
                },
            ],
            "trends": {
                "high_demand": ["CS101", "CS201", "CS301"],
                "low_utilization": ["CS499"],
                "recommendations": [
                    "Consider adding another section of CS101",
                    "Review CS499 prerequisites and marketing",
                ],
            },
        }

        return {"success": True, "data": analytics}

    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating analytics: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def manage_policy_exception(
    request_id: str, exception_type: str, department_head_id: str, rationale: str
) -> dict:
    """Grant policy exceptions for special circumstances.

    Args:
        request_id: UUID string of the request
        exception_type: Type of exception (e.g., "prerequisite_waiver", "capacity_override")
        department_head_id: UUID string of the department head
        rationale: Detailed rationale for the exception
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

        # Create policy exception record (mock implementation)
        exception_record = {
            "exception_id": f"exc-{request_id[:8]}",
            "request_id": request_id,
            "type": exception_type,
            "granted_by": department_head_id,
            "rationale": rationale,
            "granted_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

        # Update request with exception
        request.policy_exceptions = str(
            exception_record
        )  # In prod, would be proper JSON field
        request.state = "exception_granted"

        db.commit()

        return {
            "success": True,
            "data": {
                "exception": exception_record,
                "message": f"Policy exception granted: {exception_type}",
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error managing policy exception: {str(e)}",
            "data": None,
        }
    finally:
        db.close()


@tool
def view_department_schedule(department_id: str, term_id: str | None = None) -> ScheduleViewResult:
    """View complete department schedule with room and instructor assignments.

    Args:
        department_id: UUID string of the department
        term_id: Optional term UUID to filter by
    """
    try:
        db = SessionLocal()

        # Mock schedule data - would query actual department sections
        schedule = {
            "term_info": {
                "term_id": term_id or "current",
                "term_name": "Fall 2025",
                "start_date": "2025-08-25",
                "end_date": "2025-12-15",
            },
            "sections": [
                {
                    "section_id": "section-1",
                    "course_code": "CS101",
                    "course_title": "Introduction to Programming",
                    "section_code": "A1",
                    "instructor": "Dr. Smith",
                    "capacity": 25,
                    "enrolled": 23,
                    "meetings": [
                        {
                            "days": "MWF",
                            "time": "10:00-11:00",
                            "room": "SCI-101",
                            "activity": "Lecture",
                        }
                    ],
                },
                {
                    "section_id": "section-2",
                    "course_code": "CS201",
                    "course_title": "Data Structures",
                    "section_code": "A1",
                    "instructor": "Prof. Johnson",
                    "capacity": 25,
                    "enrolled": 25,
                    "meetings": [
                        {
                            "days": "TTh",
                            "time": "14:00-15:30",
                            "room": "SCI-201",
                            "activity": "Lecture",
                        }
                    ],
                },
            ],
            "summary": {
                "total_sections": 2,
                "total_capacity": 50,
                "total_enrolled": 48,
                "rooms_used": ["SCI-101", "SCI-201"],
                "instructors": ["Dr. Smith", "Prof. Johnson"],
            },
        }

        return {"success": True, "data": schedule}

    except Exception as e:
        return {
            "success": False,
            "error": f"Error viewing department schedule: {str(e)}",
            "data": None,
        }
    finally:
        db.close()
