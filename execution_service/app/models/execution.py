"""
Data models for code execution requests and responses.
"""
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """
    Request model for code execution.
    
    Attributes:
        execution_id: Unique ID for this execution
        user_id: ID of the user making the request
        code: The code to execute
        language: Programming language of the code
        timeout: Maximum execution time in seconds
        session_id: Optional ID of an existing session
        files: Optional dictionary of files to include (path -> content)
    """
    execution_id: str = Field(..., description="Unique execution ID")
    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Code to execute")
    language: str = Field("python", description="Programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    files: Optional[Dict[str, str]] = Field(None, description="Files to include")


class ExecutionResult(BaseModel):
    """
    Result model for code execution.
    
    Attributes:
        output: Standard output from the execution
        error: Standard error output (if any)
        exit_code: Process exit code
        session_id: ID of the session (if using a session)
    """
    output: str
    error: Optional[str] = None
    exit_code: int
    session_id: Optional[str] = None


class SessionRequest(BaseModel):
    """
    Request model for creating a new session.
    
    Attributes:
        language: Programming language for the session
        user_id: ID of the user creating the session
    """
    language: str = Field("python", description="Programming language for the session")
    user_id: str = Field(..., description="User ID")
