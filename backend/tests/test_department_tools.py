"""Basic working tests for department agent tools."""

import uuid
from unittest.mock import Mock, patch


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
    from langchain_core.tools import BaseTool
    
    # Verify they are LangChain tools
    assert isinstance(get_department_requests, BaseTool)
    assert isinstance(override_capacity, BaseTool)
    assert isinstance(final_approve_request, BaseTool)
    assert isinstance(get_enrollment_analytics, BaseTool)
    assert isinstance(manage_policy_exception, BaseTool)
    assert isinstance(view_department_schedule, BaseTool)


def test_get_department_requests_basic():
    """Test basic get department requests functionality."""
    from brs_backend.agents.department_tools import get_department_requests
    
    department_id = str(uuid.uuid4())
    
    # Test with proper invoke method
    with patch('brs_backend.agents.department_tools.SessionLocal') as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = get_department_requests.invoke({"department_id": department_id})
        
        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'requests')
        mock_db.close.assert_called_once()