"""Simple SmolAgents router for role-based agent access."""

from typing import Any, Dict


class SmolAgentsRouter:
    """Main router for role-based agent interactions."""
    
    def __init__(self):
        self.agents = {
            "student": "StudentAgent",
            "advisor": "AdvisorAgent", 
            "department": "DepartmentAgent"
        }
    
    def route_message(
        self, 
        user_role: str,
        user_id: str,
        message: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Route a message to the appropriate agent based on user role."""
        
        if user_role not in self.agents:
            return {
                "type": "error",
                "message": f"Unknown user role: {user_role}",
                "payload": {}
            }
        
        # Simple demo response - in production this would route to actual agents
        return {
            "type": "demo_response",
            "message": f"Hello {user_id}! This is a demo response from the {user_role} agent for: {message}",
            "payload": {
                "agent_type": user_role,
                "user_id": user_id,
                "context": context or {}
            },
            "agent_type": user_role,
            "user_id": user_id
        }
    
    def get_agent_info(self, user_role: str) -> Dict[str, Any]:
        """Get information about available agents and their capabilities."""
        
        agent_info = {
            "student": {
                "description": "Student-facing agent for course registration and scheduling",
                "capabilities": [
                    "Check pending registration requests",
                    "View current schedule",
                    "Search for course sections", 
                    "Create registration requests",
                    "Get academic information"
                ]
            },
            "advisor": {
                "description": "Academic advisor agent for student guidance",
                "capabilities": [
                    "Review student registration requests",
                    "Provide academic advice",
                    "Access student academic profiles",
                    "Approve/reject registration changes"
                ]
            },
            "department": {
                "description": "Department administrator agent for policy decisions",
                "capabilities": [
                    "Override section capacity limits",
                    "Approve policy exceptions",
                    "Generate enrollment reports",
                    "Department-level request management"
                ]
            }
        }
        
        if user_role == "all":
            return {
                "type": "agent_directory",
                "message": "Available SmolAgents",
                "payload": agent_info
            }
        elif user_role in agent_info:
            return {
                "type": "agent_info",
                "message": f"Information for {user_role} agent",
                "payload": agent_info[user_role]
            }
        else:
            return {
                "type": "error",
                "message": f"No agent information available for role: {user_role}",
                "payload": {}
            }


# Global router instance
smolagents_router = SmolAgentsRouter()