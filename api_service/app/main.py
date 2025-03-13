"""
Main application entry point for the API service.
Sets up FastAPI with routers and middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import code_execution, files, sessions

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for secure code execution in E2B sandboxes",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(code_execution.router, prefix=settings.API_V1_STR, tags=["code_execution"])
app.include_router(files.router, prefix=settings.API_V1_STR, tags=["files"])
app.include_router(sessions.router, prefix=settings.API_V1_STR, tags=["sessions"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
