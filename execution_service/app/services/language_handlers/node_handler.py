"""
Node.js language handler for code execution.
"""
from e2b import Sandbox
from app.models.execution import ExecutionResult


async def execute_node(sandbox: Sandbox, code: str) -> ExecutionResult:
    """
    Execute Node.js code in the sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: JavaScript code to execute
        
    Returns:
        Execution result
    """
    # Write code to a temporary file
    await sandbox.filesystem.write("/tmp/script.js", code)
    
    # Execute Node.js code
    process = await sandbox.process.start_command("node /tmp/script.js")
    result = await process.wait()
    
    return ExecutionResult(
        output=result.stdout,
        error=result.stderr,
        exit_code=result.exit_code
    )


class NodeHandler:
    """Node.js language handler implementation."""
    
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """
        Execute Node.js code in the sandbox.
        
        Args:
            sandbox: E2B sandbox instance
            code: JavaScript code to execute
            
        Returns:
            Execution result
        """
        return await execute_node(sandbox, code)
