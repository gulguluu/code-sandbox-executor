"""
Configuration settings for the Execution service.
Uses environment variables with sensible defaults.
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        SERVICE_NAME: Name of the service
        INTERNAL_AUTH_TOKEN: Token for internal service authentication
        INITIAL_POOL_SIZE: Initial number of sandboxes in the pool
        MAX_POOL_SIZE: Maximum number of sandboxes allowed
        DEFAULT_TIMEOUT: Default timeout for code execution in seconds
        MAX_TIMEOUT: Maximum allowed timeout for code execution in seconds
        SUPPORTED_LANGUAGES: List of supported programming languages
    """
    # Service settings
    SERVICE_NAME: str = "E2B Execution Service"
    
    # Security
    INTERNAL_AUTH_TOKEN: str = "development-token-replace-in-production"
    
    # Sandbox settings
    INITIAL_POOL_SIZE: int = 5
    MAX_POOL_SIZE: int = 20
    DEFAULT_TIMEOUT: int = 30
    MAX_TIMEOUT: int = 300
    
    # Supported languages
    SUPPORTED_LANGUAGES: List[str] = ["python", "node", "bash", "c"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()
