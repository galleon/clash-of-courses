"""Department SmolAgent implementation for course management."""

from typing import Any, Dict

from .student_tools import (
    check_pending_requests,
    get_student_info,
    search_sections,
)


class DepartmentAgent:
    """Department-facing agent for departmental oversight."""
    
    def __init__(self, department_id: str):
        self.department_id = department_id
        
    def process_message(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a department message and return structured response."""
        
        if "override" in user_message.lower() or "capacity" in user_message.lower():
            return self._handle_capacity_override(user_message, context)
        elif "department" in user_message.lower() and "requests" in user_message.lower():
            return self._review_department_requests(context)
        elif "enrollment" in user_message.lower() and "report" in user_message.lower():
            return self._generate_enrollment_report(context)
        else:
            return {
                "type": "department_info",
                "message": "Department agent ready to assist with capacity overrides and enrollment management",
                "payload": {
                    "available_actions": [
                        "capacity_override",
                        "department_request_review", 
                        "enrollment_reporting",
                        "section_management"
                    ]
                }
            }
    
    def _handle_capacity_override(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle capacity override requests."""
        section_id = context.get("section_id") if context else None
        
        if not section_id:
            return {
                "type": "error",
                "message": "Section ID required for capacity override",
                "payload": {}
            }
        
        # In a real implementation, this would update section capacity
        return {
            "type": "capacity_override",
            "message": "Capacity override processed",
            "payload": {
                "section_id": section_id,
                "action": "capacity_increased",
                "new_capacity": context.get("new_capacity", "TBD")
            }
        }
    
    def _review_department_requests(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Review all department-level requests."""
        # This would query for department-level requests requiring approval
        return {
            "type": "department_requests",
            "message": "Department requests retrieved",
            "payload": {
                "pending_requests": [],
                "capacity_overrides_needed": [],
                "policy_exceptions": []
            }
        }
    
    def _generate_enrollment_report(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate enrollment reports for the department."""
        return {
            "type": "enrollment_report",
            "message": "Enrollment report generated",
            "payload": {
                "total_enrollment": 0,
                "sections_at_capacity": 0,
                "waitlist_totals": 0,
                "popular_courses": []
            }
        }


# System prompt for department agent
DEPARTMENT_SYSTEM_PROMPT = """
You are a department administrator with authority to make policy decisions and overrides.

You can:
1. Override section capacity limits
2. Approve policy exceptions and special cases
3. Review department-level registration requests
4. Generate enrollment and capacity reports
5. Manage section offerings and scheduling conflicts

Your responsibilities:
- Ensure fair access to courses within your department
- Manage capacity and resource allocation
- Make final decisions on complex registration cases
- Monitor enrollment trends and course demand
- Coordinate with advisors on policy exceptions

You have the highest level of authority in the registration system for courses in your department. Use this authority judiciously to serve student needs while maintaining academic integrity.
"""


# Tool definitions for department agent
DEPARTMENT_TOOLS = [
    {
        "name": "override_capacity",
        "description": "Override section capacity limits for department courses",
        "parameters": {
            "type": "object",
            "properties": {
                "section_id": {
                    "type": "string",
                    "description": "UUID string of the section"
                },
                "new_capacity": {
                    "type": "integer",
                    "description": "New capacity limit"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for capacity override"
                }
            },
            "required": ["section_id", "new_capacity"]
        }
    },
    {
        "name": "approve_policy_exception",
        "description": "Approve exceptions to department policies",
        "parameters": {
            "type": "object", 
            "properties": {
                "request_id": {
                    "type": "string",
                    "description": "UUID string of the request"
                },
                "exception_type": {
                    "type": "string",
                    "description": "Type of policy exception"
                },
                "approval_reason": {
                    "type": "string",
                    "description": "Reason for approving exception"
                }
            },
            "required": ["request_id", "exception_type"]
        }
    },
    {
        "name": "generate_enrollment_report",
        "description": "Generate enrollment and capacity reports",
        "parameters": {
            "type": "object",
            "properties": {
                "term_id": {
                    "type": "string",
                    "description": "Optional term UUID to filter by"
                },
                "report_type": {
                    "type": "string",
                    "enum": ["capacity", "enrollment", "waitlist", "trends"],
                    "description": "Type of report to generate"
                }
            },
            "required": ["report_type"]
        }
    }
]