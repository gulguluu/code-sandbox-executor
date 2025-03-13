"""
Main application entry point for the Execution service.
Sets up FastAPI with endpoints for code execution and session management.
"""
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, Depends, Header, HTTPException
from e2b import Sandbox

from app.core.config import settings
from app.core.security import validate_internal_token
from app.models.execution import ExecutionRequest, SessionRequest
from app.services import sandbox_pool

# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Internal service for managing E2B sandboxes and code execution",
    version="1.0.0"
)

# Global state for sandbox management
available_sandboxes: Dict[str, List[Sandbox]] = {}
active_sandboxes: Dict[str, Sandbox] = {}
session_sandboxes: Dict[str, Sandbox] = {}
user_sessions: Dict[str, List[str]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the sandbox pool on startup."""
    global available_sandboxes
    available_sandboxes = await sandbox_pool.initialize_sandbox_pool()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up all sandboxes on shutdown."""
    await sandbox_pool.cleanup_sandboxes(
        available_sandboxes,
        active_sandboxes,
        session_sandboxes
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/execute")
async def execute_code(
    request: ExecutionRequest,
    internal_auth_token: Optional[str] = Header(None)
):
    """
    Execute code in a sandbox.
    
    Args:
        request: Execution request
        internal_auth_token: Internal authentication token
        
    Returns:
        Execution result
    """
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool.execute_code_in_sandbox(
        request,
        available_sandboxes,
        active_sandboxes,
        session_sandboxes
    )


@app.post("/sessions")
async def create_session(
    request: SessionRequest,
    internal_auth_token: Optional[str] = Header(None)
):
    """
    Create a new session with a dedicated sandbox.
    
    Args:
        request: Session request
        internal_auth_token: Internal authentication token
        
    Returns:
        Session information
    """
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool.create_session_with_sandbox(
        request,
        available_sandboxes,
        session_sandboxes,
        user_sessions
    )


@app.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    internal_auth_token: Optional[str] = Header(None)
):
    """
    End a session and return the sandbox to the pool.
    
    Args:
        session_id: ID of the session to end
        internal_auth_token: Internal authentication token
        
    Returns:
        Status information
    """
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool.end_session_and_return_sandbox(
        session_id,
        session_sandboxes,
        user_sessions,
        available_sandboxes
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
