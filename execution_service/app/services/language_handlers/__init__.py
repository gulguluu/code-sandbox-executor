"""
Language handler registry and factory function.
"""
from typing import Dict, Any, Protocol
from e2b import Sandbox
from fastapi import HTTPException

from app.models.execution import ExecutionResult


class LanguageHandler(Protocol):
    """Protocol defining the interface for language handlers."""
    
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """
        Execute code in the sandbox.
        
        Args:
            sandbox: E2B sandbox instance
            code: Code to execute
            
        Returns:
            Execution result
        """
        ...


# Import handlers here to avoid circular imports
from app.services.language_handlers.python_handler import PythonHandler
from app.services.language_handlers.node_handler import NodeHandler
from app.services.language_handlers.bash_handler import BashHandler
from app.services.language_handlers.c_handler import CHandler


# Language handler registry
_language_handlers: Dict[str, LanguageHandler] = {
    "python": PythonHandler(),
    "node": NodeHandler(),
    "javascript": NodeHandler(),  # Alias for node
    "bash": BashHandler(),
    "shell": BashHandler(),  # Alias for bash
    "c": CHandler()
}


def get_language_handler(language: str) -> LanguageHandler:
    """
    Get the appropriate language handler for the given language.
    
    Args:
        language: Programming language
        
    Returns:
        Language handler instance
        
    Raises:
        HTTPException: If language is not supported
    """
    if language not in _language_handlers:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
        
    return _language_handlers[language]
