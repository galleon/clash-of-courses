"""Chat API routes for student and advisor interactions."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from brs_backend.database.connection import get_db
from brs_backend.models.api import ChatMessage, AdvisorChatMessage, ChatResponse
from brs_backend.models.database import User
from brs_backend.agents import get_student_agent, get_advisor_agent, is_agents_available
from brs_backend.core.logging import log_detailed, logger
import re

router = APIRouter(tags=["chat"])


def clean_agent_response(response: str) -> str:
    """Clean agent response by removing thinking blocks and extracting final answer."""
    # Remove <think> blocks
    cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

    # Remove excessive whitespace
    cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
    cleaned = cleaned.strip()

    # If the response contains "Final answer:" extract only that part
    if "Final answer:" in cleaned:
        final_part = cleaned.split("Final answer:")[-1].strip()
        return final_part

    # If the response contains planning sections, try to extract the actual response
    lines = cleaned.split("\n")
    filtered_lines = []
    skip_patterns = [
        "### 1.",
        "### 2.",  # Planning sections
        "---",  # Dividers
        "```",  # Code blocks
        "Facts given",  # Planning text
        "Facts to look up",  # Planning text
        "Plan",  # Planning text
    ]

    for line in lines:
        should_skip = any(pattern in line for pattern in skip_patterns)
        if not should_skip and line.strip():
            filtered_lines.append(line)

    result = "\n".join(filtered_lines).strip()
    return result if result else cleaned


@router.post("/chat", response_model=ChatResponse)
async def student_chat(chat_message: ChatMessage, db: Session = Depends(get_db)):
    """Handle student chatbot interactions for course management."""
    log_detailed("=== STUDENT CHAT REQUEST ===")
    log_detailed(f"Student ID: {chat_message.student_id}")
    log_detailed(f"Message: '{chat_message.message}'")

    # Check if student agent is configured
    if not is_agents_available():
        logger.error("Student agent not configured")
        return ChatResponse(
            response="I'm sorry, but the AI assistant is not available right now. The system administrator needs to configure the AI service. Please use the traditional form interface or contact support.",
            action="config_error",
        )

    student_id = chat_message.student_id

    # Get student info
    student = db.query(User).filter(User.id == student_id).first()

    if not student:
        logger.error(f"Student not found for ID: {student_id}")
        return ChatResponse(response="Sorry, I couldn't find your student record.")

    log_detailed(
        f"Found student: {student.full_name} (Major: {student.major}, GPA: {student.gpa})"
    )

    try:
        # Use the student agent to handle the conversation
        # The agent maintains its own memory and has system instructions from initialization

        # Provide student context to the agent
        context_message = f"You are helping student ID {student_id} ({student.full_name}). User request: {chat_message.message}"

        log_detailed(
            f"DEBUG: student_id={student_id}, student.full_name='{student.full_name}', original_message='{chat_message.message}'"
        )
        log_detailed(f"DEBUG: context_message='{context_message}'")
        log_detailed(f"Sending message to student agent: '{context_message}'")

        student_agent = get_student_agent()
        raw_result = student_agent.run(context_message)

        # Clean the response to remove thinking blocks and planning
        result = clean_agent_response(raw_result)

        log_detailed("=== STUDENT CHAT RESPONSE ===")
        log_detailed(
            f"Agent Response: '{result[:200]}{'...' if len(result) > 200 else ''}'"
        )

        return ChatResponse(response=result, action="agent_response")

    except Exception as e:
        # Log the error for debugging
        logger.error(f"Student agent error: {str(e)}")
        logger.error(f"Model: {chat_message}")

        # Return a proper error response instead of falling back to static responses
        return ChatResponse(
            response=f"I'm experiencing technical difficulties with the AI service right now. Please try again in a moment, or use the traditional form interface. (Error: {type(e).__name__})",
            action="ai_error",
        )


@router.post("/advisor-chat", response_model=ChatResponse)
async def advisor_chat(chat_message: AdvisorChatMessage, db: Session = Depends(get_db)):
    """Handle advisor chatbot interactions for request management."""
    log_detailed("=== ADVISOR CHAT REQUEST ===")
    log_detailed(f"Advisor ID: {chat_message.advisor_id}")
    log_detailed(f"Message: '{chat_message.message}'")

    # Check if advisor agent is configured
    if not is_agents_available():
        logger.error("Advisor agent not configured")
        return ChatResponse(
            response="I'm sorry, but the AI assistant is not available right now. The system administrator needs to configure the AI service.",
            action="config_error",
        )

    advisor_id = chat_message.advisor_id

    # Get advisor info
    advisor = db.query(User).filter(User.id == advisor_id).first()

    if not advisor:
        logger.error(f"Advisor not found for ID: {advisor_id}")
        return ChatResponse(response="Sorry, I couldn't find your advisor record.")

    log_detailed(f"Found advisor: {advisor.full_name} (Role: {advisor.role})")

    try:
        # Use the advisor agent to handle the conversation
        # The agent maintains its own memory and has system instructions from initialization

        # Provide advisor context to the agent
        context_message = f"You are helping advisor ID {advisor_id} ({advisor.full_name}, Role: {advisor.role}). User request: {chat_message.message}"

        log_detailed(f"Sending message to advisor agent: '{context_message}'")

        advisor_agent = get_advisor_agent()
        raw_result = advisor_agent.run(context_message)

        # Clean the response to remove thinking blocks and planning
        result = clean_agent_response(raw_result)

        log_detailed("=== ADVISOR CHAT RESPONSE ===")
        log_detailed(
            f"Agent Response: '{result[:200]}{'...' if len(result) > 200 else ''}'"
        )

        return ChatResponse(response=result, action="agent_response")

    except Exception as e:
        # Log the error for debugging
        logger.error(f"Advisor agent error: {str(e)}")

        # Return a proper error response
        return ChatResponse(
            response=f"I'm experiencing technical difficulties with the AI service right now. Please try again in a moment. (Error: {type(e).__name__})",
            action="ai_error",
        )
