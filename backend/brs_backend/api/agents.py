"""API endpoints for SmolAgents integration."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from brs_backend.auth.jwt_auth import get_current_user
from brs_backend.agents.router import smolagents_router

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentMessageRequest(BaseModel):
    """Request model for agent messages."""

    message: str
    context: Optional[Dict[str, Any]] = None


class AgentMessageResponse(BaseModel):
    """Response model for agent messages."""

    type: str
    message: str
    payload: Dict[str, Any]
    agent_type: str
    user_id: str


@router.post("/chat", response_model=AgentMessageResponse)
async def chat_with_agent(
    request: AgentMessageRequest, current_user: dict = Depends(get_current_user)
) -> AgentMessageResponse:
    """Send a message to the appropriate agent based on user role."""
    try:
        response = smolagents_router.route_message(
            user_role=current_user.get("role", "student"),
            user_id=current_user.get("actor_id", "demo_user"),
            message=request.message,
            context=request.context or {},
        )
        return AgentMessageResponse(**response)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Agent processing error: {str(e)}"
        ) from e


@router.get("/info")
async def get_agent_info(
    role: Optional[str] = None, current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get information about available agents."""
    query_role = role or current_user.get("role", "student")
    return smolagents_router.get_agent_info(query_role)
