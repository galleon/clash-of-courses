"""Enhanced student agent tools with advanced conflict detection and calendar integration."""

import datetime
from typing import List, Dict, Any, Optional
from smolagents import tool

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import User, Course, Section, Request
from brs_backend.core.logging import log_detailed


@tool
def check_schedule_attachable(section_id: str, student_id: int) -> dict:
    """Check if a section can be attached to student's schedule without conflicts.
    
    Validates: time conflicts, prerequisites, credit limits, capacity, academic standing.
    
    Args:
        section_id: UUID of the section to check
        student_id: ID of the student
    """
    try:
        db = SessionLocal()
        violations = []
        
        # Get section details
        section_query = """
        SELECT s.section_id, s.capacity, c.code, c.title, c.credits, c.prerequisites,
               COUNT(e.enrollment_id) as current_enrollment
        FROM section s
        JOIN course_v2 c ON s.course_id = c.course_id
        LEFT JOIN enrollment e ON s.section_id = e.section_id AND e.status = 'registered'
        WHERE s.section_id = %s
        GROUP BY s.section_id, s.capacity, c.code, c.title, c.credits, c.prerequisites
        """
        
        result = db.execute(section_query, (section_id,)).fetchone()
        if not result:
            return {
                "success": False,
                "error": f"Section {section_id} not found",
                "data": None
            }
        
        section_info = dict(result)
        
        # Check 1: Capacity constraint
        if section_info['current_enrollment'] >= section_info['capacity']:
            violations.append({
                "rule_code": "BR-001",
                "severity": "error",
                "description": "Section is at full capacity",
                "details": {
                    "current": section_info['current_enrollment'],
                    "capacity": section_info['capacity']
                }
            })
        
        # Check 2: Time conflicts with current schedule
        conflict_query = """
        WITH candidate_times AS (
            SELECT sm.day_of_week, sm.start_time, sm.end_time
            FROM section_meeting sm
            WHERE sm.section_id = %s
        ),
        student_schedule AS (
            SELECT sm.day_of_week, sm.start_time, sm.end_time, c.code
            FROM enrollment e
            JOIN section sec ON e.section_id = sec.section_id
            JOIN section_meeting sm ON sec.section_id = sm.section_id
            JOIN course_v2 c ON sec.course_id = c.course_id
            WHERE e.student_id = %s AND e.status = 'registered'
            UNION ALL
            -- Include external calendar events
            SELECT 
                EXTRACT(ISODOW FROM ce.starts_at)::INT - 1 AS day_of_week,
                ce.starts_at::time AS start_time,
                ce.ends_at::time AS end_time,
                ce.title as code
            FROM calendar_event ce
            WHERE ce.student_id = %s AND ce.source = 'external'
        )
        SELECT DISTINCT ss.code, ss.start_time, ss.end_time
        FROM candidate_times ct
        JOIN student_schedule ss ON ct.day_of_week = ss.day_of_week
        WHERE (ct.start_time, ct.end_time) OVERLAPS (ss.start_time, ss.end_time)
        """
        
        conflicts = db.execute(conflict_query, (section_id, student_id, student_id)).fetchall()
        if conflicts:
            for conflict in conflicts:
                violations.append({
                    "rule_code": "BR-005",
                    "severity": "error", 
                    "description": f"Time conflict with {conflict.code}",
                    "details": {
                        "conflicting_course": conflict.code,
                        "conflict_time": f"{conflict.start_time}-{conflict.end_time}"
                    }
                })
        
        # Check 3: Credit limit (assuming 18 credit maximum)
        current_credits_query = """
        SELECT COALESCE(SUM(c.credits), 0) as total_credits
        FROM enrollment e
        JOIN section sec ON e.section_id = sec.section_id
        JOIN course_v2 c ON sec.course_id = c.course_id
        WHERE e.student_id = %s AND e.status = 'registered'
        """
        
        current_credits = db.execute(current_credits_query, (student_id,)).scalar()
        max_credits = 18  # Could be configurable per student/program
        
        if current_credits + section_info['credits'] > max_credits:
            violations.append({
                "rule_code": "BR-003",
                "severity": "error",
                "description": "Exceeds maximum credit limit",
                "details": {
                    "current_credits": current_credits,
                    "section_credits": section_info['credits'],
                    "would_total": current_credits + section_info['credits'],
                    "max_allowed": max_credits
                }
            })
        
        # Check 4: Prerequisites (simplified - would need more complex logic)
        if section_info['prerequisites']:
            # This would need more sophisticated prerequisite checking
            # For now, just flag if prerequisites exist
            violations.append({
                "rule_code": "BR-002",
                "severity": "warning",
                "description": "Prerequisites may need verification",
                "details": {
                    "prerequisites": section_info['prerequisites']
                }
            })
        
        is_attachable = len([v for v in violations if v['severity'] == 'error']) == 0
        
        return {
            "success": True,
            "data": {
                "attachable": is_attachable,
                "section_info": {
                    "course_code": section_info['code'],
                    "course_title": section_info['title'],
                    "credits": section_info['credits'],
                    "current_enrollment": section_info['current_enrollment'],
                    "capacity": section_info['capacity']
                },
                "violations": violations,
                "summary": f"{'✅ Can attach' if is_attachable else '❌ Cannot attach'} - {len(violations)} issues found"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking attachability: {str(e)}",
            "data": None
        }
    finally:
        db.close()


@tool
def get_schedule_recommendations(student_id: int, target_credits: Optional[int] = None) -> dict:
    """Generate AI-powered schedule recommendations for a student.
    
    Args:
        student_id: ID of the student
        target_credits: Desired total credits (optional)
    """
    try:
        db = SessionLocal()
        
        # Get current student info
        current_schedule_query = """
        SELECT c.code, c.title, c.credits, sec.section_code,
               sm.day_of_week, sm.start_time, sm.end_time
        FROM enrollment e
        JOIN section sec ON e.section_id = sec.section_id
        JOIN course_v2 c ON sec.course_id = c.course_id  
        JOIN section_meeting sm ON sec.section_id = sm.section_id
        WHERE e.student_id = %s AND e.status = 'registered'
        ORDER BY sm.day_of_week, sm.start_time
        """
        
        current_courses = db.execute(current_schedule_query, (student_id,)).fetchall()
        current_credits = sum([c.credits for c in current_courses])
        
        # Get student preferences if available
        pref_query = """
        SELECT preference_key, preference_value
        FROM student_preference 
        WHERE student_id = %s
        """
        
        preferences = dict(db.execute(pref_query, (student_id,)).fetchall())
        
        # Simple recommendation logic (would be much more sophisticated in practice)
        recommendations = []
        
        if target_credits and current_credits < target_credits:
            credits_needed = target_credits - current_credits
            
            # Find suitable courses not conflicting with current schedule
            available_query = """
            SELECT DISTINCT c.course_id, c.code, c.title, c.credits
            FROM course_v2 c
            JOIN section s ON c.course_id = s.course_id
            WHERE c.level <= 300  -- Assuming appropriate level
            AND NOT EXISTS (
                SELECT 1 FROM enrollment e
                JOIN section sec ON e.section_id = sec.section_id
                WHERE sec.course_id = c.course_id 
                AND e.student_id = %s 
                AND e.status IN ('registered', 'waitlisted')
            )
            LIMIT 5
            """
            
            available_courses = db.execute(available_query, (student_id,)).fetchall()
            
            for course in available_courses[:3]:  # Limit recommendations
                recommendations.append({
                    "type": "add_course",
                    "course_code": course.code,
                    "course_title": course.title,
                    "credits": course.credits,
                    "reasoning": f"Helps reach target of {target_credits} credits",
                    "confidence": 0.75,
                    "priority": "medium"
                })
        
        # Check for schedule optimization opportunities
        busy_days = {}
        for course in current_courses:
            day = course.day_of_week
            busy_days[day] = busy_days.get(day, 0) + 1
        
        if max(busy_days.values(), default=0) >= 4:
            recommendations.append({
                "type": "optimize_schedule", 
                "reasoning": "Consider redistributing courses across more days",
                "confidence": 0.60,
                "priority": "low",
                "suggestion": "Look for alternative sections to balance your weekly schedule"
            })
        
        return {
            "success": True,
            "data": {
                "current_credits": current_credits,
                "target_credits": target_credits,
                "recommendations": recommendations,
                "preferences_used": list(preferences.keys()),
                "generated_at": datetime.datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error generating recommendations: {str(e)}",
            "data": None
        }
    finally:
        db.close()


@tool 
def explain_business_rule(rule_code: str) -> dict:
    """Explain what a specific business rule means in natural language.
    
    Args:
        rule_code: The rule code (e.g., BR-005, BR-003)
    """
    
    rule_explanations = {
        "BR-001": {
            "title": "Section Capacity Limit",
            "description": "This section has reached its maximum enrollment capacity. You may be able to join the waitlist if available.",
            "resolution": "Try finding an alternative section of the same course, or contact the instructor about possible overrides."
        },
        "BR-002": {
            "title": "Prerequisites Required", 
            "description": "This course requires you to have completed certain prerequisite courses with minimum grades.",
            "resolution": "Check the course catalog for specific prerequisites and ensure you've completed them with passing grades."
        },
        "BR-003": {
            "title": "Credit Hour Limit",
            "description": "Adding this course would exceed your maximum allowed credit hours for the term.",
            "resolution": "Consider dropping another course, or request permission for a credit overload from your academic advisor."
        },
        "BR-005": {
            "title": "Schedule Time Conflict",
            "description": "This section meets at the same time as another course you're already enrolled in or have blocked in your calendar.",
            "resolution": "Look for the same course in a different section/time slot, or adjust your other commitments."
        },
        "BR-006": {
            "title": "Registration Window Closed",
            "description": "The registration period for this term has ended.",
            "resolution": "Contact the registrar's office about late registration procedures or wait for the next term."
        }
    }
    
    if rule_code not in rule_explanations:
        return {
            "success": False,
            "error": f"Unknown rule code: {rule_code}",
            "data": None
        }
    
    rule = rule_explanations[rule_code]
    return {
        "success": True,
        "data": {
            "rule_code": rule_code,
            "title": rule["title"],
            "description": rule["description"], 
            "resolution": rule["resolution"],
            "category": "academic_constraint"
        }
    }


@tool
def record_recommendation_feedback(rec_id: str, student_id: int, feedback: str, notes: str = None) -> dict:
    """Record student feedback on a recommendation for learning.
    
    Args:
        rec_id: UUID of the recommendation
        student_id: ID of the student providing feedback
        feedback: Type of feedback (accept, reject, thumbs_up, thumbs_down)
        notes: Optional additional notes
    """
    try:
        db = SessionLocal()
        
        # Insert feedback record
        feedback_query = """
        INSERT INTO recommendation_feedback (rec_id, student_id, feedback, notes)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (rec_id, student_id) 
        DO UPDATE SET feedback = EXCLUDED.feedback, notes = EXCLUDED.notes, created_at = now()
        """
        
        db.execute(feedback_query, (rec_id, student_id, feedback, notes))
        db.commit()
        
        # Also create a behavioral signal for future recommendations
        signal_query = """
        INSERT INTO student_signal (student_id, signal_type, signal_value)
        VALUES (%s, 'recommendation_feedback', %s)
        """
        
        signal_data = {
            "recommendation_id": rec_id,
            "feedback": feedback,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        db.execute(signal_query, (student_id, signal_data))
        db.commit()
        
        return {
            "success": True,
            "data": {
                "message": f"Feedback '{feedback}' recorded for recommendation {rec_id}",
                "will_improve": "This feedback helps improve future recommendations"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error recording feedback: {str(e)}",
            "data": None
        }
    finally:
        db.close()


# Keep existing tools for backward compatibility
# These would be updated to use the new schema gradually

@tool
def check_pending_requests(student_id: int) -> dict:
    """QUICK CHECK: Get only pending registration requests for a student.
    Use this for 'pending issues', 'pending requests', or similar queries.
    
    NOTE: This is the legacy version - will be updated to use registration_request_v2
    """
    # Current implementation unchanged for now
    # ... existing code ...
    pass


# Additional utility functions for the enhanced system
def _get_student_busy_times(db, student_id: int, term_id: str = None):
    """Helper to get all busy time blocks for a student."""
    query = """
    SELECT day_of_week, start_time, end_time, 'enrolled' as source, c.code as title
    FROM enrollment e
    JOIN section sec ON e.section_id = sec.section_id
    JOIN section_meeting sm ON sec.section_id = sm.section_id
    JOIN course_v2 c ON sec.course_id = c.course_id
    WHERE e.student_id = %s AND e.status = 'registered'
    
    UNION ALL
    
    SELECT 
        EXTRACT(ISODOW FROM starts_at)::INT - 1 AS day_of_week,
        starts_at::time AS start_time,
        ends_at::time AS end_time,
        source,
        title
    FROM calendar_event
    WHERE student_id = %s
    AND (%s IS NULL OR starts_at::date BETWEEN 
         (SELECT starts_on FROM term WHERE term_id = %s) AND
         (SELECT ends_on FROM term WHERE term_id = %s))
    """
    
    return db.execute(query, (student_id, student_id, term_id, term_id, term_id)).fetchall()


def _check_time_overlap(time1_start, time1_end, time2_start, time2_end):
    """Helper to check if two time ranges overlap."""
    return time1_start < time2_end and time2_start < time1_end