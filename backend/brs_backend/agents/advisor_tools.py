import datetime
from smolagents import tool

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import User, Course, Request


@tool
def get_request_details(request_id: int) -> dict:
    """Get detailed information about a specific registration request.

    Args:
        request_id: The ID of the request to get details for

    Returns:
        A dictionary containing detailed information about the request,
        including student profile, course details, and request status.
        Returns error if request not found.
    """
    try:
        db = SessionLocal()
        req = db.query(Request).filter(Request.id == request_id).first()

        if not req:
            db.close()
            return {
                "success": False,
                "error": f"Request {request_id} not found.",
                "data": None,
            }

        # Explicitly fetch course to ensure credits field is available
        course = (
            db.query(Course).filter(Course.id == req.course_id).first()
            if req.course_id
            else None
        )

        result = {
            "success": True,
            "error": None,
            "data": {
                "request": {
                    "id": req.id,
                    "student_id": req.student_id,
                    "course_id": req.course_id,
                    "request_type": req.request_type,
                    "status": req.status,
                    "justification": req.justification,
                    "created_at": req.created_at.isoformat(),
                    "updated_at": req.updated_at.isoformat()
                    if req.updated_at
                    else None,
                },
                "student": {
                    "id": req.student.id if req.student else None,
                    "full_name": req.student.full_name if req.student else "Unknown",
                    "major": req.student.major if req.student else None,
                    "gpa": req.student.gpa if req.student else None,
                    "credit_hours_completed": req.student.credit_hours_completed
                    if req.student
                    else None,
                }
                if req.student
                else None,
                "course": {
                    "id": course.id if course else None,
                    "code": course.code if course else "Unknown",
                    "title": course.name if course else "Unknown",
                    "credits": course.credits if course else None,
                    "prerequisites": course.prerequisites if course else None,
                }
                if course
                else None,
            },
        }

        db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving request details: {str(e)}",
            "data": None,
        }


@tool
def approve_request(request_id: int, advisor_id: int, rationale: str) -> dict:
    """Approve a registration request with advisor rationale.

    Args:
        request_id: The ID of the request to approve
        advisor_id: The ID of the advisor approving the request
        rationale: The reason for approving the request

    Returns:
        A dictionary confirming the approval with updated request status,
        advisor information, and approval rationale. Returns error if
        request not found or already processed.
    """
    try:
        db = SessionLocal()
        req = db.query(Request).filter(Request.id == request_id).first()

        if not req:
            db.close()
            return {
                "success": False,
                "error": f"Request {request_id} not found.",
                "data": None,
            }

        if req.status != "pending":
            db.close()
            return {
                "success": False,
                "error": f"Request {request_id} is already {req.status}.",
                "data": {"request_id": request_id, "current_status": req.status},
            }

        # Update request
        req.advisor_id = advisor_id
        req.status = "approved"
        req.justification += f"\n\n[Advisor Approval]: {rationale}"
        req.updated_at = datetime.datetime.utcnow()

        db.commit()

        # Get course details with explicit query
        course = db.query(Course).filter(Course.id == req.course_id).first()

        result = {
            "success": True,
            "error": None,
            "data": {
                "request_id": request_id,
                "student_id": req.student_id,
                "course_code": course.code if course else "Unknown",
                "course_title": course.name if course else "Unknown",
                "status": "approved",
                "advisor_id": advisor_id,
                "rationale": rationale,
                "updated_at": req.updated_at.isoformat(),
                "message": f"Request {request_id} has been approved successfully.",
            },
        }

        db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error approving request: {str(e)}",
            "data": None,
        }


@tool
def reject_request(request_id: int, advisor_id: int, rationale: str) -> dict:
    """Reject a registration request with advisor rationale.

    Args:
        request_id: The ID of the request to reject
        advisor_id: The ID of the advisor rejecting the request
        rationale: The reason for rejecting the request

    Returns:
        A dictionary confirming the rejection with updated request status,
        advisor information, and rejection rationale. Returns error if
        request not found or already processed.
    """
    try:
        db = SessionLocal()
        req = db.query(Request).filter(Request.id == request_id).first()

        if not req:
            db.close()
            return {
                "success": False,
                "error": f"Request {request_id} not found.",
                "data": None,
            }

        if req.status != "pending":
            db.close()
            return {
                "success": False,
                "error": f"Request {request_id} is already {req.status}.",
                "data": {"request_id": request_id, "current_status": req.status},
            }

        # Update request
        req.advisor_id = advisor_id
        req.status = "rejected"
        req.justification += f"\n\n[Advisor Rejection]: {rationale}"
        req.updated_at = datetime.datetime.utcnow()

        db.commit()

        # Get course details with explicit query
        course = db.query(Course).filter(Course.id == req.course_id).first()

        result = {
            "success": True,
            "error": None,
            "data": {
                "request_id": request_id,
                "student_id": req.student_id,
                "course_code": course.code if course else "Unknown",
                "course_title": course.name if course else "Unknown",
                "status": "rejected",
                "advisor_id": advisor_id,
                "rationale": rationale,
                "updated_at": req.updated_at.isoformat(),
                "message": f"Request {request_id} has been rejected.",
            },
        }

        db.close()
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Error rejecting request: {str(e)}",
            "data": None,
        }


@tool
def get_next_pending_request(advisor_id: int) -> dict:
    """Get the next pending registration request for detailed review.
    Use this when advisor says 'let's review the next request' or 'show me the first request'.

    Args:
        advisor_id: The ID of the advisor

    Returns:
        A dictionary describing the next pending request, including comprehensive
        student and course information formatted for advisor decision-making.
        The dictionary will be empty if there are no existing requests.
    """
    try:
        db = SessionLocal()

        # Get the first pending request
        req = (
            db.query(Request)
            .join(User, Request.student_id == User.id)
            .join(Course, Request.course_id == Course.id)
            .filter(Request.status == "pending")
            .order_by(Request.created_at.asc())
            .first()
        )

        if not req:
            db.close()
            return {
                "success": True,
                "error": None,
                "data": {
                    "message": "No pending requests to review at this time.",
                    "request": None,
                },
            }

        student_name = req.student.full_name if req.student else "Unknown Student"

        # Get course details with explicit query
        course = db.query(Course).filter(Course.id == req.course_id).first()
        course_info = f"{course.code} - {course.name}" if course else "Unknown Course"

        # Get student details for comprehensive review
        student = req.student
        # Explicitly fetch course to ensure credits field is available

        # Format comprehensive request description for advisor decision
        request_summary = f"""REQUEST #{req.id} - DETAILED REVIEW:

STUDENT INFORMATION:
• Name: {student_name} (ID: {req.student_id})
• Major: {student.major if student and student.major else "Not specified"}
• GPA: {student.gpa if student and student.gpa else "Not available"}
• Credits Completed: {student.credit_hours_completed if student and student.credit_hours_completed else "Not available"}

COURSE INFORMATION:
• Course: {course_info}
• Credits: {course.credits if course and course.credits else "Not specified"}
• Prerequisites: {course.prerequisites if course and course.prerequisites else "None listed"}

REQUEST DETAILS:
• Type: {req.request_type}
• Student Justification: "{req.justification}"
• Submitted: {req.created_at.strftime("%B %d, %Y at %I:%M %p")}

DECISION REQUIRED:
Do you APPROVE or REJECT this request? Please provide your rationale for the decision."""

        request_data = {
            "id": req.id,
            "student_id": req.student_id,
            "student_name": student_name,
            "student_major": student.major if student else None,
            "student_gpa": student.gpa if student else None,
            "student_credits": student.credit_hours_completed if student else None,
            "course_code": course.code if course else "Unknown",
            "course_title": course.name if course else "Unknown",
            "course_credits": course.credits if course else None,
            "course_prerequisites": course.prerequisites if course else None,
            "request_type": req.request_type,
            "justification": req.justification,
            "created_at": req.created_at.isoformat(),
            "formatted_summary": request_summary,
        }

        db.close()
        return {
            "success": True,
            "error": None,
            "data": {"message": request_summary, "request": request_data},
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving first request: {str(e)}",
            "data": None,
        }
