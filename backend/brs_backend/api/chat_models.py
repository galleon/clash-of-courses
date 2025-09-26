"""Chat API models and schemas for BRS conversational interface."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class ChatSessionRequest(BaseModel):
    """Request to create a new chat session."""

    persona: Optional[str] = (
        "auto"  # auto, student, advisor, department_head, registrar
    )


class ChatSessionResponse(BaseModel):
    """Response when creating a chat session."""

    session_id: str
    created_at: datetime


class ChatMessageRequest(BaseModel):
    """Request to send a message in a chat session."""

    session_id: str
    message: str
    attachments: List[Dict[str, Any]] = []
    client_idempotency_key: str


class ActionType(str, Enum):
    """Types of actions that can be returned by the chat agent."""

    POST = "post"
    GET = "get"
    PUT = "put"
    DELETE = "delete"


class ChatAction(BaseModel):
    """Action that can be executed by the client."""

    label: str
    type: ActionType
    endpoint: str
    body: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None


class CardType(str, Enum):
    """Types of cards that can be displayed in the chat interface."""

    WEEK_GRID = "week_grid"
    SCHEDULE_DIFF = "schedule_diff"
    REQUEST_SUMMARY = "request_summary"
    ALTERNATIVES = "alternatives"
    COURSE_INFO = "course_info"
    PREREQUISITE_TREE = "prerequisite_tree"


class ChatCard(BaseModel):
    """Card component for rich chat responses."""

    type: CardType
    payload: Dict[str, Any]


class ChatAudit(BaseModel):
    """Audit information for chat interactions."""

    correlation_id: str
    role: str
    actor_id: str
    tool_calls: List[str] = []
    timestamp: datetime


class ChatReply(BaseModel):
    """Agent reply to a chat message."""

    message: str
    cards: List[ChatCard] = []
    actions: List[ChatAction] = []
    audit: ChatAudit


class ChatMessageResponse(BaseModel):
    """Response to a chat message."""

    message_id: str
    reply: ChatReply


class StreamEvent(BaseModel):
    """Event for streaming chat responses."""

    type: str  # token, card, action, done, error
    data: Optional[Dict[str, Any]] = None


class ActionExecutionRequest(BaseModel):
    """Request to execute an action via the chat system."""

    session_id: str
    action: ChatAction


class ActionExecutionResponse(BaseModel):
    """Response from executing an action."""

    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Database models for chat persistence
from sqlalchemy import Column, String, Text, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from brs_backend.models.database import Base
import uuid


class ChatSession(Base):
    """Chat session persistence."""

    __tablename__ = "chat_session"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    persona = Column(String, default="auto")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    """Chat message persistence."""

    __tablename__ = "chat_message"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    attachments = Column(JSON)
    cards = Column(JSON)
    actions = Column(JSON)
    audit_data = Column(JSON)
    client_idempotency_key = Column(String, unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
