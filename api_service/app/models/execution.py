"""
Data models for code execution requests and responses.
"""
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    """
    Request model for code execution.
    
    Attributes:
        code: The code to execute
        language: Programming language of the code
        timeout: Maximum execution time in seconds
        session_id: Optional ID of an existing session
        files: Optional dictionary of files to include (path -> content)
    """
    code: str = Field(..., description="The code to execute")
    language: str = Field("python", description="The programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    files: Optional[Dict[str, str]] = Field(None, description="Files to include")


class CodeExecutionResponse(BaseModel):
    """
    Response model for code execution.
    
    Attributes:
        execution_id: Unique ID for this execution
        output: Standard output from the execution
        error: Standard error output (if any)
        exit_code: Process exit code
        duration_ms: Execution time in milliseconds
        session_id: ID of the session (if using a session)
    """
    execution_id: str
    output: str
    error: Optional[str] = None
    exit_code: int
    duration_ms: int
    session_id: Optional[str] = None


class SessionRequest(BaseModel):
    """
    Request model for creating a new session.
    
    Attributes:
        language: Programming language for the session
    """
    language: str = Field("python", description="Programming language for the session")


class SessionResponse(BaseModel):
    """
    Response model for session creation.
    
    Attributes:
        session_id: Unique ID for the session
        language: Programming language of the session
        message: Status message
    """
    session_id: str
    language: str
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response model.
    
    Attributes:
        detail: Error message
    """
    detail: str
