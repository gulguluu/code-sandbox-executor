"""
C language handler for code execution.
"""
import uuid
from e2b import Sandbox
from app.models.execution import ExecutionResult


async def execute_c(sandbox: Sandbox, code: str) -> ExecutionResult:
    """
    Execute C code in the sandbox.
    
    Args:
        sandbox: E2B sandbox instance
        code: C code to execute
        
    Returns:
        Execution result
    """
    # Generate unique filename to avoid conflicts
    file_id = str(uuid.uuid4())[:8]
    source_file = f"/tmp/program_{file_id}.c"
    executable = f"/tmp/program_{file_id}"
    
    # Write code to file
    await sandbox.filesystem.write(source_file, code)
    
    # Compile C code
    compile_process = await sandbox.process.start_command(f"gcc -o {executable} {source_file}")
    compile_result = await compile_process.wait()
    
    if compile_result.exit_code != 0:
        return ExecutionResult(
            output="",
            error=f"Compilation error:\n{compile_result.stderr}",
            exit_code=compile_result.exit_code
        )
    
    # Run the compiled program
    run_process = await sandbox.process.start_command(executable)
    run_result = await run_process.wait()
    
    return ExecutionResult(
        output=run_result.stdout,
        error=run_result.stderr,
        exit_code=run_result.exit_code
    )


class CHandler:
    """C language handler implementation."""
    
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """
        Execute C code in the sandbox.
        
        Args:
            sandbox: E2B sandbox instance
            code: C code to execute
            
        Returns:
            Execution result
        """
        return await execute_c(sandbox, code)
