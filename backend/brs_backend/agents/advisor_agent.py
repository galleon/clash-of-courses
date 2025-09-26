"""Advisor SmolAgent implementation for course management."""

from typing import Any, Dict

from .student_tools import (
    check_attachable,
    check_pending_requests,
    get_current_schedule,
    get_student_info,
    search_sections,
)


class AdvisorAgent:
    """Advisor-facing agent for student advising tasks."""
    
    def __init__(self, advisor_id: str):
        self.advisor_id = advisor_id
        
    def process_message(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process an advisor message and return structured response."""
        
        # Extract student_id from context or message
        student_id = context.get("student_id") if context else None
        
        if not student_id:
            return {
                "type": "error",
                "message": "Student ID is required for advisor actions",
                "payload": {}
            }
        
        # Process advisor-specific requests
        if "approve" in user_message.lower() or "review" in user_message.lower():
            return self._review_requests(student_id)
        elif "advise" in user_message.lower() or "recommend" in user_message.lower():
            return self._provide_advice(student_id, user_message)
        else:
            # Default to student info for advisors
            result = get_student_info(student_id)
            return self._format_advisor_response("student_info", result)
    
    def _review_requests(self, student_id: str) -> Dict[str, Any]:
        """Review pending requests for a student."""
        result = check_pending_requests(student_id)
        
        if result.get("success"):
            data = result.get("data", {})
            return {
                "type": "advisor_review",
                "message": f"Student has {data.get('count', 0)} pending requests to review",
                "payload": {
                    "student_id": student_id,
                    "requests": data.get("requests", []),
                    "actions": ["approve", "reject", "request_more_info"]
                }
            }
        else:
            return {
                "type": "error",
                "message": result.get("error", "Failed to retrieve requests"),
                "payload": {}
            }
    
    def _provide_advice(self, student_id: str, message: str) -> Dict[str, Any]:
        """Provide academic advice for a student."""
        # Get student context
        student_info = get_student_info(student_id)
        schedule_info = get_current_schedule(student_id)
        
        advice = []
        
        if student_info.get("success"):
            student_data = student_info.get("data", {})
            gpa = student_data.get("gpa", 0)
            standing = student_data.get("standing", "")
            
            if gpa < 2.0:
                advice.append("Consider reducing course load and focusing on core subjects")
            if standing == "probation":
                advice.append("Academic probation requires advisor approval for all changes")
        
        if schedule_info.get("success"):
            schedule_data = schedule_info.get("data", {})
            credits = schedule_data.get("total_credits", 0)
            
            if credits > 18:
                advice.append("Course load may be too heavy - consider dropping a course")
            elif credits < 12:
                advice.append("Consider adding courses to maintain full-time status")
        
        return {
            "type": "academic_advice",
            "message": "Academic advice generated based on student profile",
            "payload": {
                "student_id": student_id,
                "advice": advice,
                "student_summary": {
                    "gpa": student_info.get("data", {}).get("gpa"),
                    "standing": student_info.get("data", {}).get("standing"),
                    "credits": schedule_info.get("data", {}).get("total_credits", 0)
                }
            }
        }
    
    def _format_advisor_response(self, response_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result for advisor interface."""
        
        if not result.get("success"):
            return {
                "type": "error",
                "message": result.get("error", "Operation failed"),
                "payload": {}
            }
        
        return {
            "type": response_type,
            "message": "Information retrieved successfully", 
            "payload": result.get("data", {})
        }


# System prompt for advisor agent
ADVISOR_SYSTEM_PROMPT = """
You are an academic advisor helping students with course planning and registration issues.

You can:
1. Review and approve/reject student registration requests
2. View student academic information (GPA, standing, progress)
3. Provide academic guidance and course recommendations
4. Override registration restrictions when appropriate
5. Access comprehensive student academic history

Your role is to:
- Ensure students meet graduation requirements
- Help resolve registration conflicts and issues
- Provide guidance on course selection and academic planning
- Approve exceptions to registration policies when justified
- Monitor student academic progress and intervene when needed

Always prioritize student academic success and graduation progress. Be thorough in reviewing requests and provide clear explanations for your decisions.

When reviewing registration requests:
- Check degree requirements and prerequisites
- Consider student's academic history and standing
- Evaluate course load and scheduling conflicts
- Provide alternative suggestions when rejecting requests
"""


# Tool definitions for advisor agent  
ADVISOR_TOOLS = [
    {
        "name": "review_registration_requests",
        "description": "Review pending registration requests for students under advisement",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "UUID string of the student"
                },
                "action": {
                    "type": "string", 
                    "enum": ["approve", "reject", "request_info"],
                    "description": "Action to take on pending requests"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "get_student_profile",
        "description": "Get comprehensive academic profile for advising",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "UUID string of the student"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "provide_course_advice",
        "description": "Generate course recommendations based on degree requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "UUID string of the student"
                },
                "focus_area": {
                    "type": "string",
                    "description": "Optional focus area for recommendations"
                }
            },
            "required": ["student_id"]
        }
    }
]