"""Advisor agent orchestration using LangGraph for request review and approvals."""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from brs_backend.core.config import get_openai_model
from brs_backend.agents.advisor_tools import (
    get_pending_requests,
    explain_rule,
    propose_alternatives,
    decide_request,
    get_student_profile,
    get_advisees,
)


def create_advisor_agent():
    """Create a LangGraph advisor agent with access to advisor tools."""
    
    model = get_openai_model()
    
    tools = [
        get_pending_requests,
        explain_rule,
        propose_alternatives,
        decide_request,
        get_student_profile,
        get_advisees,
    ]
    
    system_prompt = """You are an academic advisor AI assistant helping with student registration requests and academic guidance.

Your role is to:
1. Review pending registration requests and make informed decisions
2. Explain academic rules and policies to students and colleagues
3. Propose alternative courses when original requests cannot be approved
4. Provide comprehensive student profiles for advisory meetings
5. Manage your advisee caseload effectively

Key principles:
- Always prioritize student academic success and progress toward graduation
- Apply university policies consistently but with appropriate flexibility
- Provide clear explanations for all decisions
- Consider student circumstances and academic history
- Escalate complex cases to department heads when appropriate

When reviewing requests:
- Check for prerequisite compliance
- Verify scheduling conflicts
- Consider capacity constraints
- Review student academic standing
- Assess impact on degree progress

Always provide detailed reasoning for your decisions and suggest next steps."""

    agent = create_react_agent(model, tools, state_modifier=system_prompt)
    return agent


def process_advisor_request(advisor_id: str, request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Process an advisor request using the LangGraph agent.
    
    Args:
        advisor_id: The advisor's unique identifier
        request: The advisor's request or question
        context: Optional context including student_id, request_id, etc.
        
    Returns:
        Dictionary containing the agent's response and any tool outputs
    """
    agent = create_advisor_agent()
    
    # Build the input message with context
    message_content = f"Advisor ID: {advisor_id}\n\nRequest: {request}"
    
    if context:
        message_content += f"\n\nContext: {context}"
    
    # Process the request
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message_content)]
        })
        
        # Extract the response
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
        else:
            response = "No response generated"
            
        return {
            "success": True,
            "response": response,
            "advisor_id": advisor_id,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "advisor_id": advisor_id,
            "error": f"Error processing advisor request: {str(e)}"
        }


def handle_request_review(advisor_id: str, request_id: str, action: str, reasoning: str) -> dict[str, Any]:
    """Handle a specific request review action.
    
    Args:
        advisor_id: The advisor's unique identifier
        request_id: The registration request to review
        action: The action to take (approve, deny, escalate, hold)
        reasoning: The reasoning for the decision
        
    Returns:
        Dictionary containing the decision result
    """
    agent = create_advisor_agent()
    
    message = f"""
    Please process this registration request decision:
    
    Advisor ID: {advisor_id}
    Request ID: {request_id}
    Action: {action}
    Reasoning: {reasoning}
    
    Please use the decide_request tool to process this decision and provide a summary of what happens next.
    """
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message)]
        })
        
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
        else:
            response = "Decision processed successfully"
            
        return {
            "success": True,
            "response": response,
            "action": action,
            "reasoning": reasoning,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "action": action,
            "reasoning": reasoning,
            "error": f"Error processing decision: {str(e)}"
        }


def get_student_advisory_summary(advisor_id: str, student_id: str) -> dict[str, Any]:
    """Get a comprehensive advisory summary for a student.
    
    Args:
        advisor_id: The advisor's unique identifier
        student_id: The student's unique identifier
        
    Returns:
        Dictionary containing comprehensive student information
    """
    agent = create_advisor_agent()
    
    message = f"""
    Please provide a comprehensive advisory summary for this student:
    
    Advisor ID: {advisor_id}
    Student ID: {student_id}
    
    Please use the get_student_profile tool to gather complete information and provide:
    1. Current academic status
    2. Course enrollment status
    3. Recent registration requests
    4. Degree progress assessment
    5. Any concerns or recommendations
    """
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message)]
        })
        
        messages = result.get("messages", [])
        if messages:
            response = messages[-1].content
        else:
            response = "Student summary generated"
            
        return {
            "success": True,
            "response": response,
            "student_id": student_id,
            "advisor_id": advisor_id,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "student_id": student_id,
            "advisor_id": advisor_id,
            "error": f"Error generating student summary: {str(e)}"
        }