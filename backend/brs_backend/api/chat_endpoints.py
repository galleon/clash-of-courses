"""Chat API endpoints for BRS conversational interface."""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from brs_backend.database.connection import get_db
from brs_backend.auth.jwt_auth import decode_access_token
from brs_backend.auth.jwt_handler import extract_bearer_token
from brs_backend.api.chat_models import (
    ChatSessionRequest,
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSession,
    ChatMessage,
    ActionExecutionRequest,
    ActionExecutionResponse,
    ChatReply,
    ChatAudit,
    ChatAction,
    ActionType,
)
from brs_backend.agents.student_agent import process_student_request

logger = logging.getLogger(__name__)


class JWTClaims(BaseModel):
    sub: str
    full_name: str
    user_type: str  # Changed from role to user_type
    actor_id: str
    exp: int


router = APIRouter(prefix="/chat", tags=["chat"])


def get_current_user(
    authorization: str = Header(None),
    token: str | None = Query(default=None, alias="token"),
) -> JWTClaims:
    """Extract and validate JWT claims from Authorization header or token query param."""
    # Support EventSource connections that cannot send custom headers by accepting
    # a "token" query parameter as a fallback.
    if not authorization and token:
        authorization = f"Bearer {token}"

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    try:
        payload = decode_access_token(token)
        return JWTClaims(**payload)
    except HTTPException:
        raise
    except ValidationError as exc:
        raise HTTPException(status_code=401, detail="Invalid token claims") from exc
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionRequest,
    current_user: JWTClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.sub,
        user_type=current_user.user_type,
        actor_id=current_user.actor_id,
        persona=request.persona or current_user.user_type,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return ChatSessionResponse(
        session_id=str(session.session_id), created_at=session.created_at
    )


@router.post("/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: JWTClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Send a message to the chat agent and get a response."""
    logger.info(
        f"Chat endpoint called: '{request.message}' from {current_user.full_name}"
    )
    logger.info(
        f"💬 Received message: '{request.message}' from user {current_user.full_name} ({current_user.user_type})"
    )

    # Validate session exists and belongs to user
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.session_id == uuid.UUID(request.session_id),
            ChatSession.user_id == current_user.sub,
        )
        .first()
    )

    if not session:
        logger.error(f"Chat session not found: {request.session_id}")
        raise HTTPException(
            status_code=404, detail="Chat session not found"
        )  # Check for idempotency
    logger.debug(f"Checking idempotency key: {request.client_idempotency_key}")
    existing_message = (
        db.query(ChatMessage)
        .filter(ChatMessage.client_idempotency_key == request.client_idempotency_key)
        .first()
    )

    if existing_message:
        logger.debug(
            f"Returning cached response for idempotency key: {request.client_idempotency_key}"
        )
        # Return existing response
        return ChatMessageResponse(
            message_id=str(existing_message.message_id),
            reply=ChatReply(
                message=existing_message.content,
                cards=existing_message.cards or [],
                actions=existing_message.actions or [],
                audit=existing_message.audit_data,
            ),
        )

    # Save user message
    user_message = ChatMessage(
        session_id=session.session_id,
        role="user",
        content=request.message,
        attachments=request.attachments,
        client_idempotency_key=request.client_idempotency_key,
    )
    db.add(user_message)
    db.commit()

    # Process with enhanced agent
    correlation_id = str(uuid.uuid4())

    logger.info(
        f"🤖 Processing message with LangGraph for role: {current_user.user_type}"
    )

    try:
        # Use LangGraph agent for students, fallback for other roles
        if current_user.user_type == "student":
            # Get conversation history for context
            conversation_history = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.session_id)
                .order_by(ChatMessage.created_at)
                .limit(10)  # Last 10 messages for context
                .all()
            )

            history = []
            for msg in conversation_history:
                history.append({"role": msg.role, "content": msg.content})

            # Process with LangGraph student agent
            agent_response = process_student_request(
                message=request.message,
                student_id=current_user.actor_id,
                conversation_history=history,
            )

            # Convert to ChatReply format
            reply = ChatReply(
                message=agent_response["response"],
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    user_type=current_user.user_type,
                    actor_id=current_user.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
                cards=[],  # LangGraph responses are text-based for now
                actions=[],
            )
        else:
            # Fallback for non-student roles - simple response
            reply = ChatReply(
                message="I'm currently optimized for student interactions. For advisor and department functions, please use the direct interface.",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    user_type=current_user.user_type,
                    actor_id=current_user.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
                cards=[],
                actions=[],
            )

        logger.info(f"✅ Agent response: '{reply.message[:100]}...'")

        # Save assistant response
        # Convert audit data to JSON-serializable format
        audit_dict = reply.audit.model_dump()
        # Manually convert datetime to ISO format string
        if "timestamp" in audit_dict and isinstance(audit_dict["timestamp"], datetime):
            audit_dict["timestamp"] = audit_dict["timestamp"].isoformat()

        # Convert cards and actions to JSON-serializable format
        cards_json = [card.model_dump() for card in reply.cards] if reply.cards else []
        actions_json = (
            [action.model_dump() for action in reply.actions] if reply.actions else []
        )

        assistant_message = ChatMessage(
            session_id=session.session_id,
            role="assistant",
            content=reply.message,
            cards=cards_json,
            actions=actions_json,
            audit_data=audit_dict,
        )
        db.add(assistant_message)
        db.commit()

        return ChatMessageResponse(
            message_id=str(assistant_message.message_id), reply=reply
        )

    except Exception as e:
        logger.error(f"❌ Error processing message: {str(e)}")
        # Return error response
        error_reply = ChatReply(
            message="I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=current_user.user_type,
                actor_id=current_user.actor_id,
                timestamp=datetime.now(timezone.utc),
            ),
        )

        assistant_message = ChatMessage(
            session_id=session.session_id,
            role="assistant",
            content=error_reply.message,
            audit_data=error_reply.audit.model_dump(
                mode="json"
            ),  # Use JSON serialization mode
        )
        db.add(assistant_message)
        db.commit()

        return ChatMessageResponse(
            message_id=str(assistant_message.message_id), reply=error_reply
        )


@router.get("/sse")
async def chat_sse_stream(
    session_id: str,
    current_user: JWTClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Server-Sent Events stream for real-time chat updates."""
    # Validate session
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.session_id == uuid.UUID(session_id),
            ChatSession.user_id == current_user.sub,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    async def event_stream():
        """Generate SSE events for streaming chat responses."""
        yield 'data: {"type":"connected","session_id":"' + session_id + '"}\n\n'

        # In a real implementation, this would listen for events
        # For now, just keep the connection alive
        while True:
            await asyncio.sleep(30)  # Send keepalive every 30 seconds
            yield 'data: {"type":"keepalive"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post("/action-runner", response_model=ActionExecutionResponse)
async def execute_chat_action(
    request: ActionExecutionRequest,
    current_user: JWTClaims = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    """Execute an action returned by the chat agent (centralized audit)."""
    # Validate session
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.session_id == uuid.UUID(request.session_id),
            ChatSession.user_id == current_user.sub,
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    action = request.action
    correlation_id = str(uuid.uuid4())

    try:
        # Execute the action using internal APIs
        result = await execute_internal_action(
            action=action,
            user_claims=current_user,
            correlation_id=correlation_id,
            db=db,
        )

        return ActionExecutionResponse(success=True, result=result)

    except Exception as e:
        return ActionExecutionResponse(success=False, error=str(e))


async def execute_internal_action(
    action: ChatAction, user_claims: JWTClaims, correlation_id: str, db: Session
) -> dict[str, Any] | None:
    """Execute an action by calling internal APIs."""
    # This would integrate with your existing REST endpoints
    # For now, return a mock response

    if action.endpoint.startswith("/registration-requests"):
        if action.type == ActionType.POST:
            # Mock creating a registration request
            return {
                "request_id": str(uuid.uuid4()),
                "status": "submitted",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    elif action.endpoint.startswith("/sections"):
        if "check-attachable" in action.endpoint:
            # Mock attachability check
            return {"attachable": True, "conflicts": [], "warnings": []}

    elif action.endpoint.startswith("/recommendations"):
        # Mock recommendation generation
        return {
            "recommendations": [
                {
                    "type": "swap_section",
                    "confidence": 0.85,
                    "explanation": "Better time slot availability",
                }
            ]
        }

    return {"message": "Action executed successfully"}
