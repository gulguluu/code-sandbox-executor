"""
Client for communicating with the execution service.
Handles sending requests and processing responses.
"""
import httpx
from typing import Dict, Any

from app.core.config import settings
from app.models.execution import CodeExecutionRequest, SessionRequest


async def execute_code(request: CodeExecutionRequest) -> Dict[str, Any]:
    """
    Send a code execution request to the execution service.
    
    Args:
        request: Code execution request
        
    Returns:
        Execution result as a dictionary
        
    Raises:
        Exception: If the execution service returns an error
    """
    async with httpx.AsyncClient() as client:
        headers = {"Internal-Auth-Token": settings.INTERNAL_AUTH_TOKEN}
        
        response = await client.post(
            f"{settings.EXECUTION_SERVICE_URL}/execute",
            json=request.model_dump(),
            headers=headers,
            timeout=request.timeout + 5  # Add buffer to timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Execution service error: {response.text}")
            
        return response.json()


async def create_session(language: str, user_id: str) -> Dict[str, Any]:
    """
    Create a new session in the execution service.
    
    Args:
        language: Programming language for the session
        user_id: ID of the user creating the session
        
    Returns:
        Session information as a dictionary
        
    Raises:
        Exception: If the execution service returns an error
    """
    async with httpx.AsyncClient() as client:
        headers = {"Internal-Auth-Token": settings.INTERNAL_AUTH_TOKEN}
        
        request = SessionRequest(language=language)
        request_data = request.model_dump()
        request_data["user_id"] = user_id
        
        response = await client.post(
            f"{settings.EXECUTION_SERVICE_URL}/sessions",
            json=request_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Session creation error: {response.text}")
            
        return response.json()


async def end_session(session_id: str) -> Dict[str, Any]:
    """
    End a session in the execution service.
    
    Args:
        session_id: ID of the session to end
        
    Returns:
        Status information as a dictionary
        
    Raises:
        Exception: If the execution service returns an error
    """
    async with httpx.AsyncClient() as client:
        headers = {"Internal-Auth-Token": settings.INTERNAL_AUTH_TOKEN}
        
        response = await client.delete(
            f"{settings.EXECUTION_SERVICE_URL}/sessions/{session_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Session deletion error: {response.text}")
            
        return response.json()
