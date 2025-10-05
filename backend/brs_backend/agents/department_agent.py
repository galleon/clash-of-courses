"""Department head agent orchestration using LangGraph for policy decisions and overrides."""

from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from brs_backend.core.config import get_openai_model
from brs_backend.agents.department_tools import (
    get_department_requests,
    override_capacity,
    final_approve_request,
    get_enrollment_analytics,
    manage_policy_exception,
    view_department_schedule,
)


def create_department_agent():
    """Create a LangGraph department head agent with access to administrative tools."""
    
    model = get_openai_model()
    
    tools = [
        get_department_requests,
        override_capacity,
        final_approve_request,
        get_enrollment_analytics,
        manage_policy_exception,
        view_department_schedule,
    ]
    
    system_prompt = """You are a department head AI assistant helping with administrative decisions and policy management.

Your role is to:
1. Review registration requests that require department-level approval
2. Make capacity override decisions for high-demand courses
3. Provide final approval for complex registration requests
4. Monitor enrollment analytics and trends
5. Manage policy exceptions and special circumstances
6. Oversee department course scheduling

Key principles:
- Balance student needs with resource constraints
- Maintain academic standards and policy consistency
- Consider long-term departmental goals and strategic planning
- Ensure equitable access to courses and programs
- Make data-driven decisions based on enrollment analytics

When making decisions:
- Consider overall department capacity and resource allocation
- Review historical enrollment patterns and trends
- Assess impact on faculty workload and classroom resources
- Evaluate student academic progress and degree completion
- Apply policies consistently while considering exceptional circumstances

You have the authority to:
- Override section capacity limits when justified
- Approve requests that advisors have escalated
- Create policy exceptions for special circumstances
- Make final decisions on complex registration issues
- Adjust course scheduling and resource allocation

Always provide clear reasoning for administrative decisions and document policy exceptions appropriately."""

    agent = create_react_agent(model, tools, state_modifier=system_prompt)
    return agent


def process_department_request(department_id: str, request: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Process a department head request using the LangGraph agent.
    
    Args:
        department_id: The department's unique identifier
        request: The department head's request or question
        context: Optional context including request_id, student_id, etc.
        
    Returns:
        Dictionary containing the agent's response and any tool outputs
    """
    agent = create_department_agent()
    
    # Build the input message with context
    message_content = f"Department ID: {department_id}\n\nRequest: {request}"
    
    if context:
        message_content += f"\n\nContext: {context}"
    
    # Process the request
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message_content)]
        })
        
        # Extract the response
        messages = result.get("messages", [])
        response = messages[-1].content if messages else "No response generated"
            
        return {
            "success": True,
            "response": response,
            "department_id": department_id,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "department_id": department_id,
            "error": f"Error processing department request: {str(e)}"
        }


def handle_capacity_override(department_id: str, section_id: str, new_capacity: int, justification: str) -> dict[str, Any]:
    """Handle a capacity override decision.
    
    Args:
        department_id: The department's unique identifier
        section_id: The section requiring capacity override
        new_capacity: The new capacity limit
        justification: The justification for the override
        
    Returns:
        Dictionary containing the override result
    """
    agent = create_department_agent()
    
    message = f"""
    Please process this capacity override request:
    
    Department ID: {department_id}
    Section ID: {section_id}
    New Capacity: {new_capacity}
    Justification: {justification}
    
    Please use the override_capacity tool to process this request and provide analysis of the impact.
    """
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message)]
        })
        
        messages = result.get("messages", [])
        response = messages[-1].content if messages else "Capacity override processed"
            
        return {
            "success": True,
            "response": response,
            "section_id": section_id,
            "new_capacity": new_capacity,
            "justification": justification,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "section_id": section_id,
            "new_capacity": new_capacity,
            "justification": justification,
            "error": f"Error processing capacity override: {str(e)}"
        }


def get_department_analytics_summary(department_id: str, term_id: str | None = None) -> dict[str, Any]:
    """Get comprehensive enrollment analytics for the department.
    
    Args:
        department_id: The department's unique identifier
        term_id: Optional specific term to analyze
        
    Returns:
        Dictionary containing enrollment analytics and insights
    """
    agent = create_department_agent()
    
    message = f"""
    Please provide comprehensive enrollment analytics for the department:
    
    Department ID: {department_id}
    Term ID: {term_id or "current term"}
    
    Please use the get_enrollment_analytics tool to gather data and provide:
    1. Current enrollment status and trends
    2. Course capacity utilization
    3. High-demand courses and bottlenecks
    4. Resource allocation recommendations
    5. Strategic enrollment planning insights
    """
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message)]
        })
        
        messages = result.get("messages", [])
        response = messages[-1].content if messages else "Analytics summary generated"
            
        return {
            "success": True,
            "response": response,
            "department_id": department_id,
            "term_id": term_id,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "department_id": department_id,
            "term_id": term_id,
            "error": f"Error generating analytics summary: {str(e)}"
        }


def handle_policy_exception(department_id: str, request_id: str, exception_type: str, justification: str) -> dict[str, Any]:
    """Handle a policy exception request.
    
    Args:
        department_id: The department's unique identifier
        request_id: The registration request needing exception
        exception_type: Type of exception being requested
        justification: Detailed justification for the exception
        
    Returns:
        Dictionary containing the exception decision result
    """
    agent = create_department_agent()
    
    message = f"""
    Please review this policy exception request:
    
    Department ID: {department_id}
    Request ID: {request_id}
    Exception Type: {exception_type}
    Justification: {justification}
    
    Please use the manage_policy_exception tool to evaluate and process this exception request.
    Consider the precedent this sets and the impact on departmental policies.
    """
    
    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=message)]
        })
        
        messages = result.get("messages", [])
        response = messages[-1].content if messages else "Policy exception reviewed"
            
        return {
            "success": True,
            "response": response,
            "request_id": request_id,
            "exception_type": exception_type,
            "justification": justification,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": None,
            "request_id": request_id,
            "exception_type": exception_type,
            "justification": justification,
            "error": f"Error processing policy exception: {str(e)}"
        }