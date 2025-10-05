"""Basic working tests for advisor agent tools."""

import uuid
from unittest.mock import Mock, patch


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
    from langchain_core.tools import BaseTool
    
    # Verify they are LangChain tools
    assert isinstance(get_pending_requests, BaseTool)
    assert isinstance(explain_rule, BaseTool)
    assert isinstance(propose_alternatives, BaseTool)
    assert isinstance(decide_request, BaseTool)
    assert isinstance(get_student_profile, BaseTool)
    assert isinstance(get_advisees, BaseTool)


def test_explain_rule_basic():
    """Test basic rule explanation functionality."""
    from brs_backend.agents.advisor_tools import explain_rule
    
    # Test with valid rule code
    result = explain_rule.invoke({"rule_code": "BR-001"})
    
    # Verify result structure
    assert hasattr(result, 'success')
    assert hasattr(result, 'rule_code')
    assert result.rule_code == "BR-001"
    assert result.success is True


def test_get_pending_requests_basic():
    """Test basic get pending requests functionality."""
    from brs_backend.agents.advisor_tools import get_pending_requests
    
    advisor_id = str(uuid.uuid4())
    
    # Test with proper invoke method
    with patch('brs_backend.agents.advisor_tools.SessionLocal') as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        
        result = get_pending_requests.invoke({"advisor_id": advisor_id})
        
        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'requests')
        mock_db.close.assert_called_once()


def test_get_advisees_basic():
    """Test basic get advisees functionality."""
    from brs_backend.agents.advisor_tools import get_advisees
    
    advisor_id = str(uuid.uuid4())
    
    # Test with proper invoke method
    with patch('brs_backend.agents.advisor_tools.SessionLocal') as mock_session:
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = get_advisees.invoke({"advisor_id": advisor_id})
        
        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'advisees')
        mock_db.close.assert_called_once()