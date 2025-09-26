"""Student SmolAgent implementation for course management."""

import json
from typing import Dict, Any, List
from uuid import UUID

from .student_tools_v3 import (
    get_student_info,
    check_pending_requests,
    check_attachable,
    search_sections,
    create_registration_request,
    get_current_schedule,
    propose_alternatives,
    optimize_schedule,
    build_schedule_diff
)


class StudentAgent:
    """Student-facing agent for course management tasks."""
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.tools = {
            "get_student_info": get_student_info,
            "check_pending_requests": check_pending_requests,
            "check_attachable": check_attachable,
            "search_sections": search_sections,
            "create_registration_request": create_registration_request,
            "get_current_schedule": get_current_schedule,
            "propose_alternatives": propose_alternatives,
            "optimize_schedule": optimize_schedule,
            "build_schedule_diff": build_schedule_diff
        }
        
    def process_message(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message and return structured response."""
        
        # This is where you would integrate with your LLM to understand intent
        # For now, we'll do simple keyword matching
        
        response_data = {}
        
        if "pending" in user_message.lower() or "request" in user_message.lower():
            response_data = self.tools["check_pending_requests"](self.student_id)
            
        elif "schedule" in user_message.lower():
            response_data = self.tools["get_current_schedule"](self.student_id)
            
        elif "search" in user_message.lower() and ("course" in user_message.lower() or "section" in user_message.lower()):
            # Extract course code from message (simple pattern)
            words = user_message.split()
            course_code = None
            for word in words:
                if word.upper().replace(" ", "").replace(".", "").isalnum() and len(word) >= 4:
                    course_code = word.upper()
                    break
            
            if course_code:
                response_data = self.tools["search_sections"](course_code)
            else:
                response_data = {
                    "success": False,
                    "error": "Please specify a course code to search for sections"
                }
                
        elif "info" in user_message.lower() or "gpa" in user_message.lower():
            response_data = self.tools["get_student_info"](self.student_id)
            
        else:
            response_data = {
                "success": False,
                "error": "I didn't understand your request. I can help with: checking pending requests, viewing your schedule, searching for course sections, or getting your student info."
            }
        
        # Format response according to SmolAgents pattern
        return self._format_response(user_message, response_data)
    
    def _format_response(self, user_message: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool result into SmolAgent response format."""
        
        if not tool_result.get("success", False):
            return {
                "type": "error",
                "message": tool_result.get("error", "Unknown error occurred"),
                "payload": {}
            }
        
        data = tool_result.get("data", {})
        
        # Determine response type based on data structure
        if "requests" in data:
            return {
                "type": "pending_requests",
                "message": f"You have {data.get('count', 0)} pending registration requests.",
                "payload": {
                    "count": data.get("count", 0),
                    "requests": data.get("requests", [])
                }
            }
            
        elif "schedule" in data:
            return {
                "type": "current_schedule", 
                "message": f"Your current schedule has {data.get('course_count', 0)} courses ({data.get('total_credits', 0)} credits).",
                "payload": {
                    "total_credits": data.get("total_credits", 0),
                    "course_count": data.get("course_count", 0),
                    "courses": data.get("schedule", [])
                }
            }
            
        elif "sections" in data:
            course = data.get("course", {})
            sections = data.get("sections", [])
            return {
                "type": "course_sections",
                "message": f"Found {len(sections)} sections for {course.get('code', 'Unknown')} - {course.get('title', 'Unknown')}",
                "payload": {
                    "course": course,
                    "sections": sections
                }
            }
            
        elif "gpa" in data or "credits_completed" in data:
            return {
                "type": "student_info",
                "message": f"GPA: {data.get('gpa', 'N/A')}, Credits: {data.get('credits_completed', 0)}, Standing: {data.get('standing', 'N/A')}",
                "payload": data
            }
            
        else:
            # Generic success response
            return {
                "type": "success",
                "message": "Request completed successfully",
                "payload": data
            }


# System prompt for the student agent
STUDENT_SYSTEM_PROMPT = """
You are a helpful academic advisor assistant for students. You have access to tools that let you:

1. Check student information (GPA, credits, academic standing)
2. View current course schedule
3. Check pending registration requests
4. Search for course sections
5. Create registration requests (add/drop/change sections)
6. Check if a student can attach to a specific section

Always respond in a friendly, helpful manner. If you use a tool, explain what you're doing and what the results mean. 

For registration changes, always:
- Check attachability before recommending sections
- Explain any violations or conflicts
- Guide students through the proper request process

When students ask about courses:
- Show available sections with times, instructors, and capacity
- Highlight conflicts with current schedule
- Suggest alternatives if their preferred section isn't available

Your responses should be conversational but informative. Always prioritize the student's academic success.
"""


# Tool definitions for SmolAgents integration
STUDENT_TOOLS = [
    {
        "name": "get_student_info",
        "description": "Get basic student information including GPA, credits, and academic standing",
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
        "name": "check_pending_requests", 
        "description": "Get pending registration requests for a student",
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
        "name": "search_sections",
        "description": "Search for available sections of a course",
        "parameters": {
            "type": "object", 
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "Course code (e.g. 'CS101')"
                },
                "term_id": {
                    "type": "string",
                    "description": "Optional term UUID to filter by"
                }
            },
            "required": ["course_code"]
        }
    },
    {
        "name": "get_current_schedule",
        "description": "Get the current enrolled schedule for a student",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string", 
                    "description": "UUID string of the student"
                },
                "term_id": {
                    "type": "string",
                    "description": "Optional term UUID to filter by"
                }
            },
            "required": ["student_id"]
        }
    },
    {
        "name": "check_attachable",
        "description": "Check if a student can attach to a specific section",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "UUID string of the student"
                },
                "section_id": {
                    "type": "string", 
                    "description": "UUID string of the section to check"
                }
            },
            "required": ["student_id", "section_id"]
        }
    },
    {
        "name": "create_registration_request",
        "description": "Create a registration request for a student",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "UUID string of the student"
                },
                "request_type": {
                    "type": "string",
                    "enum": ["ADD", "DROP", "CHANGE_SECTION"],
                    "description": "Type of registration request"
                },
                "to_section_id": {
                    "type": "string",
                    "description": "Optional UUID string of section to add/change to"
                },
                "from_section_id": {
                    "type": "string",
                    "description": "Optional UUID string of section to drop/change from"
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for the request"
                }
            },
            "required": ["student_id", "request_type"]
        }
    }
]