"""Chat agent that processes conversational messages and calls existing BRS APIs."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from brs_backend.auth.jwt_handler import JWTClaims
from brs_backend.api.chat_models import (
    ChatReply,
    ChatAudit,
    ChatCard,
    ChatAction,
    CardType,
    ActionType,
)


class BRSChatAgent:
    """Main chat agent for processing BRS conversations."""

    def __init__(self, role: str):
        self.role = role
        self.tools = self._get_tools_for_role(role)

    def _get_tools_for_role(self, role: str) -> Dict[str, Any]:
        """Get available tools based on user role."""
        base_tools = ["get_schedule", "get_course_info", "check_prerequisites"]

        role_tools = {
            "student": [
                "check_attachable",
                "get_recommendations",
                "create_add_request",
                "create_drop_request",
                "create_change_request",
                "get_my_requests",
                "cancel_request",
            ],
            "advisor": [
                "get_student_info",
                "review_requests",
                "approve_request",
                "reject_request",
                "get_advisees",
                "bulk_approve",
            ],
            "department_head": [
                "get_department_requests",
                "final_approve",
                "view_analytics",
                "manage_capacity",
            ],
            "registrar": [
                "system_override",
                "view_all_requests",
                "generate_reports",
                "manage_terms",
            ],
        }

        return base_tools + role_tools.get(role, [])

    async def process_message(
        self,
        message: str,
        user_claims: JWTClaims,
        session_id: str,
        correlation_id: str,
        db: Any,
    ) -> ChatReply:
        """Process a chat message and return a structured response."""

        # Simple intent detection (in production, use NLP/LLM)
        intent = self._detect_intent(message.lower())

        if intent == "greeting":
            return await self._handle_greeting(user_claims, correlation_id)
        elif intent == "schedule_inquiry":
            return await self._handle_schedule_inquiry(
                message, user_claims, correlation_id, db
            )
        elif intent == "add_course":
            return await self._handle_add_course(
                message, user_claims, correlation_id, db
            )
        elif intent == "change_section":
            return await self._handle_change_section(
                message, user_claims, correlation_id, db
            )
        elif intent == "drop_course":
            return await self._handle_drop_course(
                message, user_claims, correlation_id, db
            )
        elif intent == "request_status":
            return await self._handle_request_status(user_claims, correlation_id, db)
        else:
            return await self._handle_general_inquiry(
                message, user_claims, correlation_id
            )

    def _detect_intent(self, message: str) -> str:
        """Simple intent detection based on keywords."""
        if any(word in message for word in ["hello", "hi", "hey", "good morning"]):
            return "greeting"
        elif any(word in message for word in ["schedule", "timetable", "calendar"]):
            return "schedule_inquiry"
        elif any(
            word in message for word in ["add", "enroll", "register", "take"]
        ) and any(word in message for word in ["course", "class"]):
            return "add_course"
        elif any(word in message for word in ["change", "switch", "swap"]) and any(
            word in message for word in ["section", "time"]
        ):
            return "change_section"
        elif any(word in message for word in ["drop", "withdraw", "remove"]):
            return "drop_course"
        elif any(word in message for word in ["status", "request", "pending"]):
            return "request_status"
        else:
            return "general"

    async def _handle_greeting(
        self, user_claims: JWTClaims, correlation_id: str
    ) -> ChatReply:
        """Handle greeting messages."""
        role_messages = {
            "student": f"Hello {user_claims.full_name}! I'm here to help you with course registration. You can ask me about your schedule, add or drop courses, or check your request status.",
            "advisor": f"Welcome {user_claims.full_name}! I can help you review student requests, check advisee information, and manage approvals.",
            "department_head": f"Hello {user_claims.full_name}! I'm ready to help with department-level request reviews and final approvals.",
            "registrar": f"Welcome {user_claims.full_name}! I can assist with system-wide operations and analytics.",
        }

        return ChatReply(
            message=role_messages.get(
                user_claims.role, "Hello! How can I help you today?"
            ),
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_schedule_inquiry(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle schedule-related inquiries."""

        # Mock schedule data - in production, call actual API
        schedule_data = {
            "courses": [
                {
                    "course_code": "CS101",
                    "title": "Introduction to Programming",
                    "section": "A1",
                    "time": "MWF 10:00-11:00",
                    "instructor": "Dr. Smith",
                    "room": "SCI-101",
                },
                {
                    "course_code": "MATH201",
                    "title": "Calculus II",
                    "section": "B2",
                    "time": "TTh 14:00-15:30",
                    "instructor": "Prof. Johnson",
                    "room": "MATH-205",
                },
            ],
            "total_credits": 8,
        }

        # Create schedule card
        schedule_card = ChatCard(type=CardType.WEEK_GRID, payload=schedule_data)

        return ChatReply(
            message=f"Here's your current schedule for this term. You're enrolled in {len(schedule_data['courses'])} courses for a total of {schedule_data['total_credits']} credits.",
            cards=[schedule_card],
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                tool_calls=["get_schedule"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_add_course(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle course addition requests."""

        # Extract course info from message (simple parsing)
        course_code = self._extract_course_code(message)

        if not course_code:
            return ChatReply(
                message="I'd be happy to help you add a course! Please specify which course you'd like to add (e.g., 'I want to add CS201').",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    role=user_claims.role,
                    actor_id=user_claims.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        # Mock available sections
        sections_data = {
            "course_code": course_code,
            "sections": [
                {
                    "section_id": str(uuid.uuid4()),
                    "section_code": "A1",
                    "time": "MWF 9:00-10:00",
                    "instructor": "Dr. Williams",
                    "capacity": 25,
                    "enrolled": 18,
                    "conflicts": [],
                },
                {
                    "section_id": str(uuid.uuid4()),
                    "section_code": "A2",
                    "time": "TTh 11:00-12:30",
                    "instructor": "Dr. Garcia",
                    "capacity": 25,
                    "enrolled": 22,
                    "conflicts": ["Time conflict with MATH201"],
                },
            ],
        }

        # Create alternatives card
        alternatives_card = ChatCard(type=CardType.ALTERNATIVES, payload=sections_data)

        # Create action for best section
        best_section = sections_data["sections"][0]  # First section without conflicts
        add_action = ChatAction(
            label=f"Add {course_code} {best_section['section_code']}",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "ADD",
                "to_section_id": best_section["section_id"],
                "justification": f"Adding {course_code} as requested via chat",
            },
        )

        return ChatReply(
            message=f"I found {len(sections_data['sections'])} available sections for {course_code}. Section A1 looks like the best fit with no conflicts!",
            cards=[alternatives_card],
            actions=[add_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                tool_calls=["get_course_info", "check_attachable"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_change_section(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle section change requests."""

        # Mock current enrollment and alternatives
        change_data = {
            "current_section": {
                "course_code": "CS101",
                "section_code": "A1",
                "time": "MWF 10:00-11:00",
            },
            "requested_section": {
                "section_id": str(uuid.uuid4()),
                "section_code": "A2",
                "time": "TTh 14:00-15:30",
                "conflicts": [],
                "capacity": 25,
                "enrolled": 20,
            },
        }

        # Create schedule diff card
        diff_card = ChatCard(type=CardType.SCHEDULE_DIFF, payload=change_data)

        # Create change action
        change_action = ChatAction(
            label="Submit Section Change Request",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "CHANGE_SECTION",
                "from_section_id": "current_section_id",
                "to_section_id": change_data["requested_section"]["section_id"],
                "justification": "Section change requested via chat for better scheduling",
            },
        )

        return ChatReply(
            message="Great choice! Section A2 fits your schedule with no conflicts. Here's how your schedule would change:",
            cards=[diff_card],
            actions=[change_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                tool_calls=["check_attachable", "get_schedule_diff"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_drop_course(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle course drop requests."""

        course_code = self._extract_course_code(message)

        if not course_code:
            return ChatReply(
                message="Which course would you like to drop? Please specify the course code.",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    role=user_claims.role,
                    actor_id=user_claims.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        drop_action = ChatAction(
            label=f"Drop {course_code}",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "DROP",
                "from_section_id": "enrolled_section_id",
                "justification": f"Dropping {course_code} as requested via chat",
            },
        )

        return ChatReply(
            message=f"I can help you drop {course_code}. Please confirm if you'd like to proceed:",
            actions=[drop_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                tool_calls=["get_enrollment"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_request_status(
        self, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle request status inquiries."""

        # Mock request data
        requests_data = {
            "pending": [
                {
                    "request_id": str(uuid.uuid4()),
                    "type": "ADD",
                    "course": "CS201",
                    "section": "A1",
                    "status": "advisor_review",
                    "submitted": "2024-09-20",
                }
            ],
            "completed": [
                {
                    "request_id": str(uuid.uuid4()),
                    "type": "CHANGE_SECTION",
                    "course": "MATH201",
                    "status": "approved",
                    "completed": "2024-09-18",
                }
            ],
        }

        requests_card = ChatCard(type=CardType.REQUEST_SUMMARY, payload=requests_data)

        return ChatReply(
            message=f"You have {len(requests_data['pending'])} pending requests and {len(requests_data['completed'])} completed requests.",
            cards=[requests_card],
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                tool_calls=["get_my_requests"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_general_inquiry(
        self, message: str, user_claims: JWTClaims, correlation_id: str
    ) -> ChatReply:
        """Handle general inquiries."""
        return ChatReply(
            message="I'm here to help with course registration! You can ask me to:\n• Show your schedule\n• Add or drop courses\n• Change sections\n• Check request status\n\nWhat would you like to do?",
            audit=ChatAudit(
                correlation_id=correlation_id,
                role=user_claims.role,
                actor_id=user_claims.actor_id,
                timestamp=datetime.now(timezone.utc),
            ),
        )

    def _extract_course_code(self, message: str) -> Optional[str]:
        """Extract course code from message (simple regex would work better)."""
        words = message.upper().split()
        for word in words:
            if any(
                word.startswith(prefix)
                for prefix in ["CS", "MATH", "PHYS", "ENGL", "HIST"]
            ):
                return word
        return None


# Agent factory
def get_agent_for_role(role: str) -> BRSChatAgent:
    """Get chat agent instance for the specified role."""
    return BRSChatAgent(role)


# Main processing function
async def process_message(
    agent: BRSChatAgent,
    message: str,
    user_claims: JWTClaims,
    session_id: str,
    correlation_id: str,
    db: Any,
) -> ChatReply:
    """Process a message through the chat agent."""
    return await agent.process_message(
        message=message,
        user_claims=user_claims,
        session_id=session_id,
        correlation_id=correlation_id,
        db=db,
    )
