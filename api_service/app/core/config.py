"""
Configuration settings for the API service.
Uses environment variables with sensible defaults.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        API_V1_STR: API version prefix
        PROJECT_NAME: Name of the project
        CORS_ORIGINS: List of allowed CORS origins
        SECRET_KEY: Secret key for JWT token encryption
        ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes
        EXECUTION_SERVICE_URL: URL of the execution service
        INTERNAL_AUTH_TOKEN: Token for internal service authentication
    """
    # API settings
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Code Execution API"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "development-key-replace-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Execution service
    EXECUTION_SERVICE_URL: str = "http://localhost:8001"
    INTERNAL_AUTH_TOKEN: str = "development-token-replace-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a global settings instance
settings = Settings()
