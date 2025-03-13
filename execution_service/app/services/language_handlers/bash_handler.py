"""
Bash language handler for code execution.
"""
from e2b import Sandbox
from app.models.execution import ExecutionResult


async def execute_bash(sandbox: Sandbox, code: str) -> ExecutionResult:
    """
    Execute Bash commands in the sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: Bash commands to execute
        
    Returns:
        Execution result
    """
    # Execute bash commands directly
    process = await sandbox.process.start_command(code)
    result = await process.wait()
    
    return ExecutionResult(
        output=result.stdout,
        error=result.stderr,
        exit_code=result.exit_code
    )


class BashHandler:
    """Bash language handler implementation."""
    
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """
        Execute Bash commands in the sandbox.
        
        Args:
            sandbox: E2B sandbox instance
            code: Bash commands to execute
            
        Returns:
            Execution result
        """
        return await execute_bash(sandbox, code)
