"""
Python language handler for code execution.
"""
from e2b import Sandbox
from app.models.execution import ExecutionResult


async def execute_python(sandbox: Sandbox, code: str) -> ExecutionResult:
    """
    Execute Python code in the sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: Python code to execute
        
    Returns:
        Execution result
    """
    # Execute Python code directly
    process = await sandbox.process.start_python(code=code)
    result = await process.wait()
    
    return ExecutionResult(
        output=result.stdout,
        error=result.stderr,
        exit_code=result.exit_code
    )


class PythonHandler:
    """Python language handler implementation."""
    
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """
        Execute Python code in the sandbox.
        
        Args:
            sandbox: E2B sandbox instance
            code: Python code to execute
            
        Returns:
            Execution result
        """
        return await execute_python(sandbox, code)
