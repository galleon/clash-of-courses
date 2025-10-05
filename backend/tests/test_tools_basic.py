"""Simple test to verify LangChain tools work correctly."""

import pytest
from langchain_core.tools import BaseTool

def test_student_tools_import():
    """Test that student tools can be imported."""
    from brs_backend.agents.student_tools import (
        get_current_schedule,
        check_course_attachability, 
        enroll_in_course,
        drop_course,
        get_schedule_ical,
        search_available_courses
    )
    
    # Verify they are LangChain tools
    assert isinstance(get_current_schedule, BaseTool)
    assert isinstance(check_course_attachability, BaseTool)
    assert isinstance(enroll_in_course, BaseTool)
    assert isinstance(drop_course, BaseTool)
    assert isinstance(get_schedule_ical, BaseTool)
    assert isinstance(search_available_courses, BaseTool)

def test_advisor_tools_import():
    """Test that advisor tools can be imported."""
    from brs_backend.agents.advisor_tools import (
        get_pending_requests,
        explain_rule,
        propose_alternatives,
        decide_request,
        get_student_profile,
        get_advisees
    )
    
    # Verify they are LangChain tools
    assert isinstance(get_pending_requests, BaseTool)
    assert isinstance(explain_rule, BaseTool)
    assert isinstance(propose_alternatives, BaseTool)
    assert isinstance(decide_request, BaseTool)
    assert isinstance(get_student_profile, BaseTool)
    assert isinstance(get_advisees, BaseTool)

def test_department_tools_import():
    """Test that department tools can be imported."""
    from brs_backend.agents.department_tools import (
        get_department_requests,
        override_capacity,
        final_approve_request,
        get_enrollment_analytics,
        manage_policy_exception,
        view_department_schedule
    )
    
    # Verify they are LangChain tools
    assert isinstance(get_department_requests, BaseTool)
    assert isinstance(override_capacity, BaseTool)
    assert isinstance(final_approve_request, BaseTool)
    assert isinstance(get_enrollment_analytics, BaseTool)
    assert isinstance(manage_policy_exception, BaseTool)
    assert isinstance(view_department_schedule, BaseTool)

def test_tool_invocation_basic():
    """Test basic tool invocation using invoke method."""
    from brs_backend.agents.advisor_tools import explain_rule
    
    # Test with a valid rule code
    result = explain_rule.invoke({"rule_code": "PREREQ"})
    
    # Should return a structured result
    assert hasattr(result, 'success')
    assert hasattr(result, 'rule_code')
    
    # Test with invalid rule code
    result = explain_rule.invoke({"rule_code": "INVALID"})
    assert hasattr(result, 'success')