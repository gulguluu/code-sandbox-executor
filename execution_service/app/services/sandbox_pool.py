"""
Sandbox pool manager for E2B sandboxes.
Handles sandbox creation, allocation, and lifecycle management.
"""
import asyncio
import uuid
import time
import logging
from typing import Dict, List, Optional, Any
from e2b import Sandbox
from fastapi import HTTPException

from app.core.config import settings
from app.models.execution import ExecutionRequest, SessionRequest, ExecutionResult
from app.services.language_handlers import get_language_handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_sandbox() -> Optional[Sandbox]:
    """
    Create a new E2B sandbox.
    
    Returns:
        Sandbox instance or None if creation failed
    """
    try:
        # Create E2B sandbox
        # In production, you might want different template IDs for different languages
        # or custom templates with pre-installed packages
        return await Sandbox.create()
    except Exception as e:
        logger.error(f"Error creating sandbox: {str(e)}")
        return None


async def reset_sandbox(sandbox: Sandbox) -> bool:
    """
    Reset a sandbox to clean state.
    
    Args:
        sandbox: Sandbox to reset
        
    Returns:
        True if reset successful, False otherwise
    """
    try:
        # Clear temporary files and user home directory
        await sandbox.process.start_command("rm -rf /tmp/* && rm -rf /home/user/*")
        return True
    except Exception as e:
        logger.error(f"Error resetting sandbox: {str(e)}")
        return False


async def manage_sandbox_pool(
    available_sandboxes: Dict[str, List[Sandbox]],
    language: str
) -> Optional[Sandbox]:
    """
    Get a sandbox from the pool or create a new one.
    
    Args:
        available_sandboxes: Dictionary of available sandboxes by language
        language: Programming language
        
    Returns:
        Sandbox instance or None if no sandbox available
    """
    # First try to get from available pool
    if available_sandboxes.get(language, []):
        return available_sandboxes[language].pop(0)
        
    # If no available sandbox, create a new one
    return await create_sandbox()


# Main sandbox pool manager
async def execute_code_in_sandbox(
    request: ExecutionRequest,
    available_sandboxes: Dict[str, List[Sandbox]],
    active_sandboxes: Dict[str, Sandbox],
    session_sandboxes: Dict[str, Sandbox]
) -> Dict[str, Any]:
    """
    Execute code in a sandbox.
    
    Args:
        request: Execution request
        available_sandboxes: Dictionary of available sandboxes by language
        active_sandboxes: Dictionary of active sandboxes
        session_sandboxes: Dictionary of session sandboxes
        
    Returns:
        Execution result
    """
    # Validate timeout
    timeout = min(request.timeout, settings.MAX_TIMEOUT)
    
    # Check if using existing session
    if request.session_id and request.session_id in session_sandboxes:
        sandbox = session_sandboxes[request.session_id]
        sandbox_id = request.session_id
    else:
        # Get sandbox from pool
        sandbox = await manage_sandbox_pool(available_sandboxes, request.language)
        if not sandbox:
            raise HTTPException(status_code=503, detail="No sandbox available")
            
        # Store sandbox in active sandboxes
        sandbox_id = str(uuid.uuid4())
        active_sandboxes[sandbox_id] = sandbox
        
        # Add language metadata
        sandbox.metadata = {"language": request.language}
        
    try:
        # Get the appropriate language handler
        language_handler = get_language_handler(request.language)
        
        # Handle file uploads if any
        if request.files:
            for file_path, file_content in request.files.items():
                await sandbox.filesystem.write(file_path, file_content)
        
        # Execute code with timeout
        start_time = time.time()
        result = await asyncio.wait_for(
            language_handler.execute(sandbox, request.code),
            timeout=timeout
        )
        
        # Format result
        output_data = {
            "output": result.output,
            "error": result.error,
            "exit_code": result.exit_code
        }
        
        # Add session ID if from session
        if request.session_id:
            output_data["session_id"] = request.session_id
            
        # If not a session, return sandbox to pool
        if not request.session_id:
            asyncio.create_task(return_sandbox_to_pool(
                sandbox_id, 
                sandbox, 
                request.language, 
                active_sandboxes, 
                available_sandboxes
            ))
            
        return output_data
        
    except asyncio.TimeoutError:
        # Handle timeout
        if not request.session_id:
            asyncio.create_task(return_sandbox_to_pool(
                sandbox_id, 
                sandbox, 
                request.language, 
                active_sandboxes, 
                available_sandboxes,
                reset=True
            ))
        return {"error": "Execution timed out", "output": "", "exit_code": -1}
        
    except Exception as e:
        # Handle other errors
        logger.error(f"Execution error: {str(e)}")
        if not request.session_id:
            asyncio.create_task(return_sandbox_to_pool(
                sandbox_id, 
                sandbox, 
                request.language, 
                active_sandboxes, 
                available_sandboxes,
                reset=True
            ))
        return {"error": str(e), "output": "", "exit_code": -1}


async def return_sandbox_to_pool(
    sandbox_id: str,
    sandbox: Sandbox,
    language: str,
    active_sandboxes: Dict[str, Sandbox],
    available_sandboxes: Dict[str, List[Sandbox]],
    reset: bool = True
):
    """
    Return a sandbox to the pool.
    
    Args:
        sandbox_id: ID of the sandbox
        sandbox: Sandbox instance
        language: Programming language
        active_sandboxes: Dictionary of active sandboxes
        available_sandboxes: Dictionary of available sandboxes by language
        reset: Whether to reset the sandbox state
    """
    if sandbox_id in active_sandboxes:
        # Remove from active sandboxes
        active_sandboxes.pop(sandbox_id, None)
        
        try:
            if reset:
                # Reset sandbox state
                await reset_sandbox(sandbox)
                
            # Return to available pool
            if language not in available_sandboxes:
                available_sandboxes[language] = []
            available_sandboxes[language].append(sandbox)
        except Exception as e:
            logger.error(f"Error returning sandbox: {str(e)}")
            await sandbox.close()


async def create_session_with_sandbox(
    request: SessionRequest,
    available_sandboxes: Dict[str, List[Sandbox]],
    session_sandboxes: Dict[str, Sandbox],
    user_sessions: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Create a persistent session with a dedicated sandbox.
    
    Args:
        request: Session request
        available_sandboxes: Dictionary of available sandboxes by language
        session_sandboxes: Dictionary of session sandboxes
        user_sessions: Dictionary of user sessions
        
    Returns:
        Session information
    """
    # Get sandbox from pool
    sandbox = await manage_sandbox_pool(available_sandboxes, request.language)
    if not sandbox:
        raise HTTPException(status_code=503, detail="No sandbox available")
        
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Store in session sandboxes
    session_sandboxes[session_id] = sandbox
    
    # Track user sessions
    if request.user_id not in user_sessions:
        user_sessions[request.user_id] = []
    user_sessions[request.user_id].append(session_id)
    
    # Add metadata
    sandbox.metadata = {
        "language": request.language,
        "user_id": request.user_id,
        "created_at": time.time()
    }
    
    return {
        "session_id": session_id,
        "language": request.language,
        "message": "Session created successfully"
    }


async def end_session_and_return_sandbox(
    session_id: str,
    session_sandboxes: Dict[str, Sandbox],
    user_sessions: Dict[str, List[str]],
    available_sandboxes: Dict[str, List[Sandbox]]
) -> Dict[str, Any]:
    """
    End a session and return the sandbox to the pool.
    
    Args:
        session_id: ID of the session to end
        session_sandboxes: Dictionary of session sandboxes
        user_sessions: Dictionary of user sessions
        available_sandboxes: Dictionary of available sandboxes by language
        
    Returns:
        Status information
    """
    if session_id not in session_sandboxes:
        raise HTTPException(status_code=404, detail="Session not found")
        
    sandbox = session_sandboxes.pop(session_id)
    language = sandbox.metadata.get("language", "python")
    user_id = sandbox.metadata.get("user_id")
    
    # Remove from user sessions
    if user_id and user_id in user_sessions:
        if session_id in user_sessions[user_id]:
            user_sessions[user_id].remove(session_id)
            
    # Reset and return to pool
    try:
        await reset_sandbox(sandbox)
        if language not in available_sandboxes:
            available_sandboxes[language] = []
        available_sandboxes[language].append(sandbox)
    except Exception as e:
        logger.error(f"Error returning session sandbox: {str(e)}")
        await sandbox.close()
        
    return {
        "success": True,
        "message": "Session ended successfully"
    }


async def initialize_sandbox_pool() -> Dict[str, List[Sandbox]]:
    """
    Initialize the sandbox pool with pre-warmed sandboxes.
    
    Returns:
        Dictionary of available sandboxes by language
    """
    available_sandboxes = {lang: [] for lang in settings.SUPPORTED_LANGUAGES}
    
    # Create initial pool of sandboxes
    for language in settings.SUPPORTED_LANGUAGES:
        for _ in range(settings.INITIAL_POOL_SIZE // len(settings.SUPPORTED_LANGUAGES)):
            sandbox = await create_sandbox()
            if sandbox:
                available_sandboxes[language].append(sandbox)
                
    return available_sandboxes


async def cleanup_sandboxes(
    available_sandboxes: Dict[str, List[Sandbox]],
    active_sandboxes: Dict[str, Sandbox],
    session_sandboxes: Dict[str, Sandbox]
):
    """
    Cleanup all sandboxes when shutting down.
    
    Args:
        available_sandboxes: Dictionary of available sandboxes by language
        active_sandboxes: Dictionary of active sandboxes
        session_sandboxes: Dictionary of session sandboxes
    """
    # Close all available sandboxes
    for language in available_sandboxes:
        for sandbox in available_sandboxes[language]:
            await sandbox.close()
            
    # Close all active sandboxes
    for sandbox_id in active_sandboxes:
        await active_sandboxes[sandbox_id].close()
        
    # Close all session sandboxes
    for session_id in session_sandboxes:
        await session_sandboxes[session_id].close()
