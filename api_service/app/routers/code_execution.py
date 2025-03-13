"""
Router for code execution endpoints.
Handles code execution, session creation, and session management.
"""
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.core.auth import get_current_user
from app.models.execution import CodeExecutionRequest, CodeExecutionResponse, SessionResponse
from app.services import execution_client

# Create router
router = APIRouter()


@router.post("/code_interpreter/run", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute code in a sandbox.
    
    Args:
        request: Code execution request
        user_id: ID of the authenticated user
        
    Returns:
        Execution results
        
    Raises:
        HTTPException: If execution fails
    """
    try:
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        # Record start time
        start_time = time.time()
        
        # Add execution ID and user ID to request
        execution_request = request.model_dump()
        execution_request["execution_id"] = execution_id
        execution_request["user_id"] = user_id
        
        # Execute code
        result = await execution_client.execute_code(CodeExecutionRequest(**execution_request))
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Format response
        response = {
            "execution_id": execution_id,
            "output": result.get("output", ""),
            "error": result.get("error"),
            "exit_code": result.get("exit_code", -1),
            "duration_ms": duration_ms,
            "session_id": result.get("session_id")
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code_interpreter/sessions", response_model=SessionResponse)
async def create_session(
    language: str = "python",
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a new execution session.
    
    Args:
        language: Programming language for the session
        user_id: ID of the authenticated user
        
    Returns:
        Session information
        
    Raises:
        HTTPException: If session creation fails
    """
    try:
        result = await execution_client.create_session(language, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/code_interpreter/sessions/{session_id}")
async def end_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    End an execution session.
    
    Args:
        session_id: ID of the session to end
        user_id: ID of the authenticated user
        
    Returns:
        Status information
        
    Raises:
        HTTPException: If session deletion fails
    """
    try:
        await execution_client.end_session(session_id)
        return {"success": True, "message": "Session ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
