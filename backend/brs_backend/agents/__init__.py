"""Agent initialization and configuration."""

import openai
from smolagents import ToolCallingAgent, OpenAIServerModel

from brs_backend.core.config import settings
from brs_backend.core.logging import logger
from brs_backend.agents.student_tools import (
    get_student_info,
    get_available_courses,
    check_course_sections,
    create_registration_request,
    check_pending_requests,
    get_current_enrollments,
    find_course_by_code,
)
from brs_backend.agents.advisor_tools import (
    get_request_details,
    approve_request,
    reject_request,
    get_next_pending_request,
)


# Global agent instances
student_agent = None
advisor_agent = None
llm_model = None


def validate_api_configuration():
    """Validate OpenAI API configuration and connectivity at startup."""
    if not settings.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not found in environment variables")
        return False

    if not settings.OPENAI_API_BASE:
        logger.error("❌ OPENAI_API_BASE not found in environment variables")
        return False

    if not settings.OPENAI_MODEL:
        logger.error("❌ OPENAI_MODEL not found in environment variables")
        return False

    # Test API connectivity
    try:
        test_client = openai.OpenAI(
            api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE
        )

        # Test with a minimal request
        response = test_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
            timeout=10.0,
        )
        # Just verify we got a response
        if response:
            logger.info("✅ API connection validated successfully")
            logger.info(f"   - API Base: {settings.OPENAI_API_BASE}")
            logger.info(f"   - Model: {settings.OPENAI_MODEL}")
            logger.info(
                f"   - API Key: {'*' * (len(settings.OPENAI_API_KEY) - 8) + settings.OPENAI_API_KEY[-8:] if len(settings.OPENAI_API_KEY) > 8 else '***'}"
            )
            return True

    except Exception as e:
        logger.error(f"❌ API connection validation failed: {e}")
        logger.error(f"   - API Base: {settings.OPENAI_API_BASE}")
        logger.error(f"   - Model: {settings.OPENAI_MODEL}")
        logger.error("   - Check your API key and base URL configuration")
        return False


def initialize_agents():
    """Initialize the AI agents with their respective tools."""
    global student_agent, advisor_agent, llm_model

    # Validate API configuration first
    if not validate_api_configuration():
        logger.error(
            "❌ API configuration validation failed - agents will not be available"
        )
        return

    try:
        # Initialize the LLM model
        llm_model = OpenAIServerModel(
            model_id=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            api_base=settings.OPENAI_API_BASE,
        )
        logger.info(f"Initialized SmolagentsAI model: {settings.OPENAI_MODEL}")

        # Student agent with student-specific tools
        student_tools = [
            create_registration_request,  # Course registration - prioritized first for "add course" requests
            check_pending_requests,  # Quick pending check
            get_current_enrollments,  # Quick enrollment check
            find_course_by_code,  # Course lookup for registration
            get_student_info,  # Comprehensive info - fallback
            get_available_courses,
            check_course_sections,
        ]

        student_agent = ToolCallingAgent(
            tools=student_tools, model=llm_model, planning_interval=4, max_steps=7
        )

        # Advisor agent with advisor-specific tools
        advisor_tools = [
            get_next_pending_request,  # For reviewing individual requests with full details
            get_request_details,
            approve_request,
            reject_request,
        ]

        advisor_agent = ToolCallingAgent(
            tools=advisor_tools, model=llm_model, planning_interval=5, max_steps=5
        )

        logger.info("Student and advisor agents initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize agents: {e}")
        llm_model = None
        student_agent = None
        advisor_agent = None


def get_student_agent():
    """Get the student agent instance."""
    return student_agent


def get_advisor_agent():
    """Get the advisor agent instance."""
    return advisor_agent


def is_agents_available():
    """Check if agents are available."""
    return student_agent is not None and advisor_agent is not None
