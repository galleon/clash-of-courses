"""LangGraph student agent - Orchestration and conversation handling."""

import uuid
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from brs_backend.core.config import settings
from brs_backend.agents.student_tools import (
    get_current_schedule,
    check_course_attachability,
    enroll_in_course,
    drop_course,
    get_schedule_ical,
    search_available_courses,
)


def create_student_agent():
    """Create a LangGraph ReAct agent for student interactions."""
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0.0, api_key=settings.OPENAI_API_KEY)

    # Define available tools
    tools = [
        get_current_schedule,
        check_course_attachability,
        enroll_in_course,
        drop_course,
        get_schedule_ical,
        search_available_courses,
    ]

    # Create the ReAct agent using LangGraph's built-in functionality
    agent = create_react_agent(model=llm, tools=tools)

    return agent


# Don't initialize the student agent at module level - create fresh instances
# student_agent = create_student_agent()


def process_student_request(
    message: str, student_id: str, conversation_history: list[dict[str, str]] = None
) -> dict[str, Any]:
    """Process a student request using the LangGraph agent.

    Args:
        message: User message
        student_id: Student ID for context
        conversation_history: Previous conversation messages

    Returns:
        Agent response with structured data
    """
    # Create a fresh agent instance for each request
    agent = create_student_agent()

    # Convert conversation history to messages
    messages = []

    # Add system message first
    system_prompt = f"""You are a helpful academic advisor assistant specializing in student course registration.
Current student ID: {student_id}

Your capabilities include:
- Checking current student schedules with detailed course information
- Verifying course enrollment eligibility and conflicts
- Enrolling students in courses with conflict detection
- Dropping courses and updating schedules
- Providing iCal calendar exports
- Searching available courses

Always provide structured, helpful responses using the available tools.
When enrollment actions are taken, always call get_current_schedule() afterward to provide updated information."""

    messages.append(HumanMessage(content=system_prompt))

    if conversation_history:
        for msg in conversation_history:
            # Skip if this is the current message (avoid duplication)
            if msg["content"] == message:
                continue

            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current message
    messages.append(HumanMessage(content=message))

    # Run the agent - create_react_agent expects {"messages": [...]}
    result = agent.invoke({"messages": messages})

    # Extract final response
    final_message = result["messages"][-1]

    return {
        "response": final_message.content
        if hasattr(final_message, "content")
        else str(final_message),
        "student_id": student_id,
        "conversation_id": str(uuid.uuid4()),
        "metadata": {"timestamp": datetime.now().isoformat()},
        "timestamp": datetime.now().isoformat(),
    }