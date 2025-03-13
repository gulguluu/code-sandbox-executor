"""
Monitoring utilities for the Execution service.
Tracks resource usage and performance metrics.
"""
import time
import psutil
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_system_resources() -> Dict[str, Any]:
    """
    Get current system resource usage.
    
    Returns:
        Dictionary with CPU, memory, and disk usage
    """
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }


class ExecutionMetrics:
    """Simple metrics tracker for code execution."""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.initial_resources = get_system_resources()
        self.final_resources: Optional[Dict[str, Any]] = None
        
    def stop(self):
        """Stop tracking and calculate final metrics."""
        self.end_time = time.time()
        self.final_resources = get_system_resources()
        
    @property
    def duration_ms(self) -> int:
        """Get execution duration in milliseconds."""
        if self.end_time is None:
            return int((time.time() - self.start_time) * 1000)
        return int((self.end_time - self.start_time) * 1000)
    
    @property
    def resource_usage(self) -> Dict[str, Any]:
        """Get resource usage during execution."""
        if self.final_resources is None:
            current = get_system_resources()
        else:
            current = self.final_resources
            
        return {
            "cpu_percent_change": current["cpu_percent"] - self.initial_resources["cpu_percent"],
            "memory_percent_change": current["memory_percent"] - self.initial_resources["memory_percent"],
            "disk_percent_change": current["disk_percent"] - self.initial_resources["disk_percent"]
        }
    
    def log_metrics(self, execution_id: str, language: str):
        """
        Log execution metrics.
        
        Args:
            execution_id: ID of the execution
            language: Programming language used
        """
        if self.end_time is None:
            self.stop()
            
        resource_usage = self.resource_usage
        logger.info(
            f"Execution {execution_id} ({language}) completed in {self.duration_ms}ms. "
            f"CPU: {resource_usage['cpu_percent_change']:.1f}%, "
            f"Memory: {resource_usage['memory_percent_change']:.1f}%, "
            f"Disk: {resource_usage['disk_percent_change']:.1f}%"
        )


async def track_execution(execution_id: str, language: str, func, *args, **kwargs):
    """
    Track execution of a function with metrics.
    
    Args:
        execution_id: ID of the execution
        language: Programming language used
        func: Function to execute
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function
    """
    metrics = ExecutionMetrics()
    
    try:
        result = await func(*args, **kwargs)
        return result
    finally:
        metrics.stop()
        metrics.log_metrics(execution_id, language)
