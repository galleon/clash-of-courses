"""Utility functions for the application."""

from typing import Any, Dict, Optional


def create_tool_response(
    success: bool, 
    data: Optional[Any] = None, 
    error: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized tool response format.
    
    Args:
        success: Whether the operation was successful
        data: The response data (can be any type)
        error: Error message if operation failed
        message: Optional user-friendly message
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "success": success,
        "error": error,
        "data": data
    }
    
    if message and isinstance(data, dict):
        response["data"]["message"] = message
    elif message and data is None:
        response["data"] = {"message": message}
        
    return response


def create_success_response(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """Create a successful tool response."""
    return create_tool_response(success=True, data=data, message=message)


def create_error_response(error: str, data: Any = None) -> Dict[str, Any]:
    """Create an error tool response."""
    return create_tool_response(success=False, error=error, data=data)
