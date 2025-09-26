"""Student agent tools for course management - Updated V3."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from brs_backend.database.connection import SessionLocal
from brs_backend.models.database import (
    Course,
    Enrollment,
    RegistrationRequest,
    Section,
    SectionMeeting,
    Student,
)


def get_student_info(student_id: str) -> dict:
    """Get basic student information including GPA, credits, and status.
    
    Args:
        student_id: UUID string of the student
    """
    try:
        db = SessionLocal()
        
        student = db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        if not student:
            return {
                "success": False,
                "error": "Student not found",
                "data": None
            }
        
        return {
            "success": True,
            "data": {
                "student_id": str(student.student_id),
                "external_sis_id": student.external_sis_id,
                "gpa": float(student.gpa) if student.gpa else None,
                "credits_completed": student.credits_completed,
                "standing": student.standing,
                "student_status": student.student_status,
                "financial_status": student.financial_status,
                "study_type": student.study_type
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error retrieving student info: {str(e)}",
            "data": None
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
                RegistrationRequest.state.in_(["submitted", "advisor_review", "dept_review"])
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
                "created_at": req.created_at.isoformat() if req.created_at else None
            }
            
            if to_section:
                request_data["to_course"] = {
                    "code": to_section.course.code,
                    "title": to_section.course.title,
                    "section_code": to_section.section_code
                }
                
            if from_section:
                request_data["from_course"] = {
                    "code": from_section.course.code,
                    "title": from_section.course.title,
                    "section_code": from_section.section_code
                }
                
            requests_data.append(request_data)
        
        return {
            "success": True,
            "data": {
                "count": len(pending_requests),
                "requests": requests_data
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking pending requests: {str(e)}",
            "data": None
        }
    finally:
        db.close()


 
def check_attachable(student_id: str, section_id: str) -> dict:
    """Check if a student can attach to a specific section (eligibility check).
    
    Args:
        student_id: UUID string of the student
        section_id: UUID string of the section to check
    """
    try:
        db = SessionLocal()
        
        # Get student and section
        student = db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        section = db.query(Section).filter(Section.section_id == UUID(section_id)).first()
        
        if not student:
            return {"success": False, "error": "Student not found", "violations": []}
        if not section:
            return {"success": False, "error": "Section not found", "violations": []}
            
        violations = []
        
        # Check capacity
        enrolled_count = db.query(Enrollment).filter(
            Enrollment.section_id == UUID(section_id),
            Enrollment.status == "registered"
        ).count()
        
        if enrolled_count >= section.capacity:
            violations.append({
                "rule_code": "BR-002", 
                "message": "Section at capacity",
                "severity": "error"
            })
        
        # Check for time conflicts with current enrollments
        student_enrollments = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered"
            )
            .all()
        )
        
        # Get target section meetings
        target_meetings = db.query(SectionMeeting).filter(
            SectionMeeting.section_id == UUID(section_id)
        ).all()
        
        for enrollment in student_enrollments:
            enrolled_meetings = db.query(SectionMeeting).filter(
                SectionMeeting.section_id == enrollment.section_id
            ).all()
            
            # Check for time conflicts (simplified - would need proper TSRANGE overlap check)
            for target_meeting in target_meetings:
                for enrolled_meeting in enrolled_meetings:
                    if (target_meeting.day_of_week == enrolled_meeting.day_of_week):
                        violations.append({
                            "rule_code": "BR-005",
                            "message": f"Time conflict with {enrollment.section.course.code}",
                            "severity": "error"
                        })
        
        # Check academic standing
        if student.standing in ["probation", "suspended"]:
            violations.append({
                "rule_code": "BR-001",
                "message": f"Student on {student.standing} - advisor approval required",
                "severity": "warning"
            })
        
        return {
            "success": True,
            "attachable": len([v for v in violations if v["severity"] == "error"]) == 0,
            "violations": violations,
            "data": {
                "section": {
                    "section_id": str(section.section_id),
                    "course_code": section.course.code,
                    "course_title": section.course.title,
                    "section_code": section.section_code,
                    "capacity": section.capacity,
                    "enrolled": enrolled_count,
                    "available": section.capacity - enrolled_count
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error checking attachability: {str(e)}",
            "violations": []
        }
    finally:
        db.close()



def search_sections(course_code: str, term_id: Optional[str] = None) -> dict:
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
                "data": None
            }
        
        # Build section query
        query = db.query(Section).filter(Section.course_id == course.course_id)
        if term_id:
            query = query.filter(Section.term_id == UUID(term_id))
        
        sections = query.all()
        
        sections_data = []
        for section in sections:
            # Get enrollment count
            enrolled_count = db.query(Enrollment).filter(
                Enrollment.section_id == section.section_id,
                Enrollment.status == "registered"
            ).count()
            
            # Get meetings
            meetings = db.query(SectionMeeting).filter(
                SectionMeeting.section_id == section.section_id
            ).all()
            
            meetings_data = []
            for meeting in meetings:
                meetings_data.append({
                    "day_of_week": meeting.day_of_week,
                    "activity": meeting.activity,
                    "room": meeting.room.name if meeting.room else None
                })
            
            sections_data.append({
                "section_id": str(section.section_id),
                "section_code": section.section_code,
                "instructor": section.instructor.name if section.instructor else "TBD",
                "capacity": section.capacity,
                "enrolled": enrolled_count,
                "available": section.capacity - enrolled_count,
                "meetings": meetings_data
            })
        
        return {
            "success": True,
            "data": {
                "course": {
                    "code": course.code,
                    "title": course.title,
                    "credits": course.credits
                },
                "sections": sections_data
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching sections: {str(e)}",
            "data": None
        }
    finally:
        db.close()



def create_registration_request(
    student_id: str,
    request_type: str,
    to_section_id: Optional[str] = None,
    from_section_id: Optional[str] = None,
    reason: Optional[str] = None
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
        student = db.query(Student).filter(Student.student_id == UUID(student_id)).first()
        if not student:
            return {
                "success": False,
                "error": "Student not found",
                "data": None
            }
        
        # Validate sections exist if provided
        if to_section_id:
            to_section = db.query(Section).filter(Section.section_id == UUID(to_section_id)).first()
            if not to_section:
                return {
                    "success": False,
                    "error": "Target section not found",
                    "data": None
                }
        
        if from_section_id:
            from_section = db.query(Section).filter(Section.section_id == UUID(from_section_id)).first()
            if not from_section:
                return {
                    "success": False,
                    "error": "Source section not found", 
                    "data": None
                }
        
        # Create the registration request
        registration_request = RegistrationRequest(
            student_id=UUID(student_id),
            type=request_type,
            to_section_id=UUID(to_section_id) if to_section_id else None,
            from_section_id=UUID(from_section_id) if from_section_id else None,
            reason=reason,
            state="submitted",
            created_at=datetime.utcnow()
        )
        
        db.add(registration_request)
        db.commit()
        db.refresh(registration_request)
        
        return {
            "success": True,
            "data": {
                "request_id": str(registration_request.request_id),
                "type": registration_request.type,
                "state": registration_request.state,
                "reason": registration_request.reason,
                "created_at": registration_request.created_at.isoformat(),
                "message": f"Registration request created successfully. Request ID: {registration_request.request_id}"
            }
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Error creating registration request: {str(e)}",
            "data": None
        }
    finally:
        db.close()



def get_current_schedule(student_id: str, term_id: Optional[str] = None) -> dict:
    """Get the current enrolled schedule for a student.
    
    Args:
        student_id: UUID string of the student  
        term_id: Optional term UUID to filter by
    """
    try:
        db = SessionLocal()
        
        # Build enrollment query
        query = (
            db.query(Enrollment)
            .join(Section, Enrollment.section_id == Section.section_id)
            .join(Course, Section.course_id == Course.course_id)
            .filter(
                Enrollment.student_id == UUID(student_id),
                Enrollment.status == "registered"
            )
        )
        
        if term_id:
            query = query.filter(Section.term_id == UUID(term_id))
        
        enrollments = query.all()
        
        schedule_data = []
        total_credits = 0
        
        for enrollment in enrollments:
            section = enrollment.section
            course = section.course
            
            # Get meetings for this section
            meetings = db.query(SectionMeeting).filter(
                SectionMeeting.section_id == section.section_id
            ).all()
            
            meetings_data = []
            for meeting in meetings:
                meetings_data.append({
                    "day_of_week": meeting.day_of_week,
                    "activity": meeting.activity,
                    "room": meeting.room.name if meeting.room else None
                })
            
            schedule_data.append({
                "enrollment_id": str(enrollment.enrollment_id),
                "course_code": course.code,
                "course_title": course.title,
                "credits": course.credits,
                "section_code": section.section_code,
                "instructor": section.instructor.name if section.instructor else "TBD",
                "meetings": meetings_data,
                "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
            })
            
            total_credits += course.credits
        
        return {
            "success": True,
            "data": {
                "student_id": student_id,
                "term_id": term_id,
                "total_credits": total_credits,
                "course_count": len(enrollments),
                "schedule": schedule_data
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error getting current schedule: {str(e)}",
            "data": None
        }
    finally:
        db.close()


# Placeholder tools for the complete SmolAgents architecture

def propose_alternatives(student_id: str, course_code: str, preferences: dict = None) -> dict:
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
            "message": "Alternative section proposal feature coming soon"
        }
    }


 
def optimize_schedule(student_id: str, target_courses: list, preferences: dict = None) -> dict:
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
            "message": "Schedule optimization feature coming soon"
        }
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
            "score_delta": 0.0
        }
    }