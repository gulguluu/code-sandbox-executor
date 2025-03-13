"""
Security utilities for the Execution service.
"""
from fastapi import HTTPException, status
from app.core.config import settings


def validate_internal_token(token: str) -> bool:
    """
    Validate the internal authentication token.
    
    Args:
        token: Token to validate
        
    Returns:
        True if token is valid
        
    Raises:
        HTTPException: If token is invalid
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No authentication token provided"
        )
        
    if token != settings.INTERNAL_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication token"
        )
    
    return True
