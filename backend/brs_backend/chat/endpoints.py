"""
Simple Chat API endpoints for BRS
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from ..auth.jwt_auth import decode_access_token

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
security = HTTPBearer()

# In-memory storage for demo (use database in production)
chat_sessions = {}
chat_messages = {}


class ChatSessionCreate(BaseModel):
    persona: str = "auto"


class ChatSessionResponse(BaseModel):
    session_id: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    session_id: str
    message: str
    client_idempotency_key: str


class ChatMessageResponse(BaseModel):
    message_id: str
    reply: Dict[str, Any]


class ActionRequest(BaseModel):
    session_id: str
    action: Dict[str, Any]


def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token"""
    try:
        payload = decode_access_token(token.credentials)
        return payload
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from exc


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate, current_user=Depends(get_current_user)
):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "user": current_user,
        "created_at": datetime.now(UTC),
        "messages": [],
    }
    chat_sessions[session_id] = session

    return ChatSessionResponse(session_id=session_id, created_at=session["created_at"])


@router.post("/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreate, current_user=Depends(get_current_user)
):
    """Send a message to the chat"""
    session = chat_sessions.get(message_data.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
        )

    # Simple response logic based on user role and message
    message_id = str(uuid.uuid4())
    user_role = current_user.get("role", "student")
    user_message = message_data.message.lower()

    # Generate a simple response based on the message content
    response_message = generate_response(user_message, user_role)
    cards = generate_cards(user_message, user_role)
    actions = generate_actions(user_message, user_role)

    reply = {
        "message": response_message,
        "cards": cards,
        "actions": actions,
        "audit": {"role": user_role, "correlation_id": f"corr_{message_id}"},
    }

    # Store the message
    session["messages"].append(
        {
            "id": message_id,
            "user_message": message_data.message,
            "assistant_reply": reply,
            "timestamp": datetime.now(UTC),
        }
    )

    return ChatMessageResponse(message_id=message_id, reply=reply)


def generate_response(message: str, role: str) -> str:
    """Generate a simple response based on message content and user role"""
    if "schedule" in message or "calendar" in message:
        if role == "student":
            return "I can help you view your current schedule and suggest changes. Here's what I found:"
        elif role == "advisor":
            return "I can help you review student schedules and approve registration requests."
    elif "course" in message or "class" in message:
        return "I can help you find information about courses and sections. What specific course are you interested in?"
    elif ("register" in message or "add" in message) and role == "student":
        return "I can help you register for courses. Let me check what's available and if there are any conflicts."
    elif "hello" in message or "hi" in message:
        return f"Hello! I'm your BRS assistant. As a {role}, I can help you with course registration, schedules, and academic planning. What would you like to do?"
    else:
        return f"I understand you're looking for help with: {message}. As a {role}, I can assist with course registration, scheduling, and academic planning. Could you be more specific about what you need?"


def generate_cards(message: str, role: str) -> List[Dict[str, Any]]:
    """Generate UI cards based on message content"""
    cards = []

    if "schedule" in message:
        cards.append(
            {
                "type": "week_grid",
                "payload": {
                    "days": [
                        {
                            "day": "Monday",
                            "slots": [
                                {"time": "9:00", "course": "CS101", "room": "Room 201"},
                                {
                                    "time": "14:00",
                                    "course": "MATH201",
                                    "room": "Room 105",
                                },
                            ],
                        },
                        {
                            "day": "Wednesday",
                            "slots": [
                                {"time": "9:00", "course": "CS101", "room": "Room 201"},
                                {
                                    "time": "11:00",
                                    "course": "ENG101",
                                    "room": "Room 301",
                                },
                            ],
                        },
                    ],
                    "conflicts": [],
                },
            }
        )

    if "course" in message or "cs101" in message:
        cards.append(
            {
                "type": "course_info",
                "payload": {
                    "code": "CS101",
                    "title": "Introduction to Computer Science",
                    "credits": 3,
                    "description": "Fundamental concepts of computer science including programming, algorithms, and data structures.",
                    "prerequisites": ["MATH100"],
                },
            }
        )

        cards.append(
            {
                "type": "alternatives",
                "payload": {
                    "alternatives": [
                        {
                            "course": "CS101",
                            "section": "A1",
                            "schedule": "MWF 9:00-10:00",
                            "instructor": "Dr. Smith",
                            "available_seats": 5,
                            "capacity": 25,
                        },
                        {
                            "course": "CS101",
                            "section": "A2",
                            "schedule": "TTH 11:00-12:30",
                            "instructor": "Dr. Johnson",
                            "available_seats": 12,
                            "capacity": 30,
                        },
                    ]
                },
            }
        )

    return cards


def generate_actions(message: str, role: str) -> List[Dict[str, Any]]:
    """Generate action buttons based on message content"""
    actions = []

    if ("register" in message or "add" in message) and role == "student":
        actions.append(
            {
                "label": "Register for CS101 A1",
                "type": "post",
                "endpoint": "/api/registration-requests",
                "body": {
                    "type": "ADD",
                    "to_section_id": "cs101_a1_section_id",
                    "justification": "Adding required course for degree program",
                },
            }
        )

    if "schedule" in message and role == "student":
        actions.append(
            {
                "label": "Get Recommendations",
                "type": "post",
                "endpoint": "/api/recommendations",
                "body": {"type": "optimize_schedule"},
            }
        )

    return actions


@router.post("/action-runner")
async def execute_action(
    action_request: ActionRequest, current_user=Depends(get_current_user)
):
    """Execute an action on behalf of the user"""
    # This would normally call the actual API endpoints
    # For demo purposes, return a success message
    return {
        "success": True,
        "message": f"Action '{action_request.action.get('label', 'Unknown')}' executed successfully",
    }
