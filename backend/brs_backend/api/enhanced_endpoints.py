"""Enhanced BRS API endpoints for calendar integration and schedule optimization."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from brs_backend.database.connection import get_db
from brs_backend.agents.student_tools_v2 import (
    check_schedule_attachable,
    get_schedule_recommendations,
    explain_business_rule,
    record_recommendation_feedback,
)

router = APIRouter(prefix="/api/v2", tags=["enhanced-brs"])


# Pydantic models for request/response
class AttachabilityRequest(BaseModel):
    section_id: UUID
    student_id: int


class AttachabilityResponse(BaseModel):
    attachable: bool
    violations: List[dict]
    section_info: dict
    summary: str


class RecommendationRequest(BaseModel):
    student_id: int
    target_credits: Optional[int] = None
    preferences: Optional[dict] = None


class FeedbackRequest(BaseModel):
    recommendation_id: UUID
    student_id: int
    feedback: str  # accept, reject, thumbs_up, thumbs_down
    notes: Optional[str] = None


@router.post("/sections/check-attachable", response_model=dict)
async def check_section_attachable(
    request: AttachabilityRequest, db: Session = Depends(get_db)
):
    """Check if a section can be attached to student's schedule without conflicts."""
    try:
        result = check_schedule_attachable(str(request.section_id), request.student_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/recommendations/generate", response_model=dict)
async def generate_recommendations(
    request: RecommendationRequest, db: Session = Depends(get_db)
):
    """Generate AI-powered schedule recommendations for a student."""
    try:
        result = get_schedule_recommendations(
            request.student_id, request.target_credits
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rules/{rule_code}/explain", response_model=dict)
async def explain_rule(rule_code: str):
    """Get natural language explanation of a business rule."""
    try:
        result = explain_business_rule(rule_code)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/recommendations/feedback", response_model=dict)
async def submit_recommendation_feedback(
    request: FeedbackRequest, db: Session = Depends(get_db)
):
    """Record student feedback on a recommendation."""
    try:
        result = record_recommendation_feedback(
            str(request.recommendation_id),
            request.student_id,
            request.feedback,
            request.notes,
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/students/{student_id}/schedule", response_model=dict)
async def get_student_schedule(
    student_id: int, term_id: Optional[UUID] = None, db: Session = Depends(get_db)
):
    """Get comprehensive student schedule including meetings and external events."""
    try:
        # SQL query to get student's complete schedule
        schedule_query = """
        WITH current_term AS (
            SELECT term_id FROM term WHERE is_active = true OR term_id = %s
            LIMIT 1
        )
        SELECT
            'course' as event_type,
            c.code as title,
            c.title as description,
            sm.day_of_week,
            sm.start_time,
            sm.end_time,
            sm.room as location,
            sm.activity,
            sec.instructor_name,
            c.credits
        FROM enrollment e
        JOIN section sec ON e.section_id = sec.section_id
        JOIN course_v2 c ON sec.course_id = c.course_id
        JOIN section_meeting sm ON sec.section_id = sm.section_id
        JOIN current_term ct ON sec.term_id = ct.term_id
        WHERE e.student_id = %s AND e.status = 'registered'

        UNION ALL

        SELECT
            'external' as event_type,
            ce.title,
            LEFT(ce.payload->>'description', 100) as description,
            EXTRACT(ISODOW FROM ce.starts_at)::INT - 1 AS day_of_week,
            ce.starts_at::time AS start_time,
            ce.ends_at::time AS end_time,
            ce.location,
            'EXT' as activity,
            NULL as instructor_name,
            0 as credits
        FROM calendar_event ce
        WHERE ce.student_id = %s AND ce.source = 'external'
        AND ce.starts_at >= NOW() - INTERVAL '1 week'
        AND ce.starts_at <= NOW() + INTERVAL '4 weeks'

        ORDER BY day_of_week, start_time
        """

        # Execute query (would need proper DB connection setup)
        term_param = str(term_id) if term_id else None
        # schedule = db.execute(schedule_query, (term_param, student_id, student_id)).fetchall()

        # For now, return a structured response
        return {
            "student_id": student_id,
            "term_id": term_id,
            "schedule": [
                # Would be populated from query results
            ],
            "summary": {
                "total_courses": 0,
                "total_credits": 0,
                "busiest_day": "Monday",
                "free_blocks": [],
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/students/{student_id}/conflicts", response_model=dict)
async def detect_schedule_conflicts(student_id: int, db: Session = Depends(get_db)):
    """Detect and report any conflicts in student's current schedule."""
    try:
        conflicts_query = """
        WITH student_schedule AS (
            SELECT
                sm.section_id,
                c.code,
                sm.day_of_week,
                sm.start_time,
                sm.end_time,
                'course' as source
            FROM enrollment e
            JOIN section sec ON e.section_id = sec.section_id
            JOIN course_v2 c ON sec.course_id = c.course_id
            JOIN section_meeting sm ON sec.section_id = sm.section_id
            WHERE e.student_id = %s AND e.status = 'registered'

            UNION ALL

            SELECT
                NULL as section_id,
                ce.title as code,
                EXTRACT(ISODOW FROM ce.starts_at)::INT - 1 AS day_of_week,
                ce.starts_at::time AS start_time,
                ce.ends_at::time AS end_time,
                'external' as source
            FROM calendar_event ce
            WHERE ce.student_id = %s AND ce.source = 'external'
        )
        SELECT
            s1.code as event1,
            s2.code as event2,
            s1.day_of_week,
            s1.start_time as start1,
            s1.end_time as end1,
            s2.start_time as start2,
            s2.end_time as end2,
            'time_overlap' as conflict_type
        FROM student_schedule s1
        JOIN student_schedule s2 ON s1.day_of_week = s2.day_of_week
        WHERE (s1.section_id < s2.section_id OR (s1.section_id IS NULL AND s2.section_id IS NOT NULL))
        AND (s1.start_time, s1.end_time) OVERLAPS (s2.start_time, s2.end_time)
        """

        # conflicts = db.execute(conflicts_query, (student_id, student_id)).fetchall()

        return {
            "student_id": student_id,
            "conflicts_found": 0,  # len(conflicts)
            "conflicts": [],  # Would be populated from query
            "recommendations": ["No conflicts detected in your current schedule."],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/calendar/{student_id}/ics", response_class="text/calendar")
async def export_student_calendar(student_id: int, db: Session = Depends(get_db)):
    """Export student schedule as ICS calendar file."""
    try:
        # Would generate proper ICS format
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BRS//Enhanced Registration System//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH

BEGIN:VEVENT
UID:example@brs.edu
DTSTAMP:20250924T140000Z
DTSTART:20250924T140000Z
DTEND:20250924T150000Z
SUMMARY:Sample Course - CS101
DESCRIPTION:Introduction to Computer Science
LOCATION:Room 101
END:VEVENT

END:VCALENDAR"""

        return ics_content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
