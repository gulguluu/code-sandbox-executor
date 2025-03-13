# E2B Code Execution Environment Architecture for LLM Integration

## Overview

This document outlines the architecture for a secure code execution service that integrates with LLMs using E2B sandboxes. The system consists of two virtual machines within the same VPC:

1. **API Management VM**: Handles external requests, authentication, and API compatibility
2. **Xeon Execution VM**: Manages E2B sandboxes and executes code in isolated environments

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                               VPC                                     │
│                                                                       │
│  ┌─────────────────────────────┐      ┌───────────────────────────┐  │
│  │      API Management VM      │      │       Xeon Execution VM   │  │
│  │                             │      │                           │  │
│  │ ┌─────────────────────────┐ │      │ ┌─────────────────────┐  │  │
│  │ │ API Gateway/Load Balancer│ │      │ │  E2B Agent Service  │  │  │
│  │ └───────────┬─────────────┘ │      │ └──────────┬──────────┘  │  │
│  │             │               │      │            │             │  │
│  │ ┌───────────▼─────────────┐ │      │ ┌──────────▼──────────┐  │  │
│  │ │  Management Service     │ │      │ │ Sandbox Manager     │  │  │
│  │ │  - Auth handling        │ │      │ │ - Sandbox creation  │  │  │
│  │ │  - API endpoints        │◄┼──────┼─┤ - Resource control  │  │  │
│  │ │  - Request validation   │ │      │ │ - Execution handling│  │  │
│  │ │  - Response formatting  │ │      │ │ - Language support  │  │  │
│  │ └─────────────────────────┘ │      │ └──────────┬──────────┘  │  │
│  │                             │      │            │             │  │
│  │                             │      │ ┌──────────▼──────────┐  │  │
│  │                             │      │ │ E2B Sandboxes       │  │  │
│  │                             │      │ │ ┌────┐ ┌────┐ ┌────┐│  │  │
│  │                             │      │ │ │ S1 │ │ S2 │ │ S3 ││  │  │
│  │                             │      │ │ └────┘ └────┘ └────┘│  │  │
│  └─────────────────────────────┘      └───────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. API Management VM

#### File Structure
```
/api-service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── code_execution.py    # Code execution endpoints
│   │   ├── files.py             # File management endpoints
│   │   └── sessions.py          # Session management endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication utils
│   │   ├── config.py            # Configuration settings
│   │   └── security.py          # Security utils
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution.py         # Execution request/response models
│   │   └── error.py             # Error models
│   └── services/
│       ├── __init__.py
│       └── execution_client.py   # Client for execution service
├── requirements.txt
└── Dockerfile
```

#### Docker/Deployment Files

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt**
```
fastapi==0.104.1
pydantic==2.4.2
uvicorn==0.23.2
python-jose==3.3.0
python-multipart==0.0.6
httpx==0.25.0
```

### 2. Xeon Execution VM

#### File Structure
```
/execution-service/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Configuration settings
│   │   └── security.py          # Internal auth utils
│   ├── models/
│   │   ├── __init__.py
│   │   └── execution.py         # Execution models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sandbox_pool.py      # E2B sandbox pool management
│   │   └── language_handlers/   # Language-specific execution handlers
│   │       ├── __init__.py
│   │       ├── python_handler.py
│   │       ├── node_handler.py
│   │       ├── bash_handler.py
│   │       └── c_handler.py
│   └── utils/
│       ├── __init__.py
│       └── monitoring.py        # Resource monitoring
├── requirements.txt
└── Dockerfile
```

#### Docker/Deployment Files

**Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for language support
RUN apt-get update && apt-get install -y \
    build-essential \
    nodejs \
    npm \
    && apt-get clean

COPY ./app /app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt**
```
fastapi==0.104.1
pydantic==2.4.2
uvicorn==0.23.2
e2b==0.12.0
asyncio==3.4.3
```

## Implementation Code

### API Management VM

#### app/main.py
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import code_execution, files, sessions

app = FastAPI(
    title="Code Execution API",
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
app.include_router(code_execution.router, prefix="/v1", tags=["code_execution"])
app.include_router(files.router, prefix="/v1", tags=["files"])
app.include_router(sessions.router, prefix="/v1", tags=["sessions"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### app/core/config.py
```python
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Code Execution API"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-in-production-use-env-var"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Execution service
    EXECUTION_SERVICE_URL: str = "http://xeon-vm-internal-address:8000"
    INTERNAL_AUTH_TOKEN: str = "your-secure-token-replace-in-production"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### app/core/auth.py
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    return user_id
```

#### app/models/execution.py
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="The code to execute")
    language: str = Field("python", description="The programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    files: Optional[Dict[str, str]] = Field(None, description="Files to include")

class CodeExecutionResponse(BaseModel):
    execution_id: str
    output: str
    error: Optional[str] = None
    exit_code: int
    duration_ms: int
    session_id: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
```

#### app/services/execution_client.py
```python
import httpx
import asyncio
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.execution import CodeExecutionRequest, CodeExecutionResponse

class ExecutionServiceClient:
    def __init__(self):
        self.base_url = settings.EXECUTION_SERVICE_URL
        self.auth_token = settings.INTERNAL_AUTH_TOKEN
        
    async def execute_code(self, request: CodeExecutionRequest) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Auth-Token": self.auth_token}
            
            response = await client.post(
                f"{self.base_url}/execute",
                json=request.dict(),
                headers=headers,
                timeout=request.timeout + 5  # Add buffer to timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Execution service error: {response.text}")
                
            return response.json()
            
    async def create_session(self, language: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Auth-Token": self.auth_token}
            
            response = await client.post(
                f"{self.base_url}/sessions",
                json={"language": language},
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Session creation error: {response.text}")
                
            return response.json()
            
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            headers = {"Internal-Auth-Token": self.auth_token}
            
            response = await client.delete(
                f"{self.base_url}/sessions/{session_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Session deletion error: {response.text}")
                
            return response.json()

execution_client = ExecutionServiceClient()
```

#### app/routers/code_execution.py
```python
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any

from app.core.auth import get_current_user
from app.models.execution import CodeExecutionRequest, CodeExecutionResponse
from app.services.execution_client import execution_client

router = APIRouter()

@router.post("/code_interpreter/run", response_model=CodeExecutionResponse)
async def execute_code(
    request: CodeExecutionRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    try:
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        
        # Record start time
        start_time = time.time()
        
        # Execute code
        execution_request = request.dict()
        execution_request["execution_id"] = execution_id
        execution_request["user_id"] = user_id
        
        result = await execution_client.execute_code(CodeExecutionRequest(**execution_request))
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Format response
        response = {
            "execution_id": execution_id,
            "output": result.get("output", ""),
            "error": result.get("error"),
            "exit_code": result.get("exit_code", -1),
            "duration_ms": duration_ms,
            "session_id": result.get("session_id")
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/code_interpreter/sessions", response_model=Dict[str, Any])
async def create_session(
    language: str = "python",
    user_id: str = Depends(get_current_user)
):
    try:
        result = await execution_client.create_session(language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/code_interpreter/sessions/{session_id}")
async def end_session(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    try:
        result = await execution_client.end_session(session_id)
        return {"success": True, "message": "Session ended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Xeon Execution VM

#### app/main.py
```python
from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Optional

from app.core.config import settings
from app.core.security import validate_internal_token
from app.models.execution import ExecutionRequest, SessionRequest
from app.services.sandbox_pool import SandboxPoolManager

app = FastAPI(
    title="E2B Execution Service",
    description="Internal service for managing E2B sandboxes and code execution",
    version="1.0.0"
)

# Initialize sandbox pool manager
sandbox_pool_manager = SandboxPoolManager()

@app.on_event("startup")
async def startup_event():
    await sandbox_pool_manager.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await sandbox_pool_manager.cleanup()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/execute")
async def execute_code(
    request: ExecutionRequest,
    internal_auth_token: Optional[str] = Header(None)
):
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool_manager.execute_code(request)

@app.post("/sessions")
async def create_session(
    request: SessionRequest,
    internal_auth_token: Optional[str] = Header(None)
):
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool_manager.create_session(request)

@app.delete("/sessions/{session_id}")
async def end_session(
    session_id: str,
    internal_auth_token: Optional[str] = Header(None)
):
    # Validate internal token
    validate_internal_token(internal_auth_token)
    
    return await sandbox_pool_manager.end_session(session_id)
```

#### app/core/config.py
```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Service settings
    SERVICE_NAME: str = "E2B Execution Service"
    
    # Security
    INTERNAL_AUTH_TOKEN: str = "your-secure-token-replace-in-production"
    
    # Sandbox settings
    INITIAL_POOL_SIZE: int = 5
    MAX_POOL_SIZE: int = 20
    DEFAULT_TIMEOUT: int = 30
    MAX_TIMEOUT: int = 300
    
    # Supported languages
    SUPPORTED_LANGUAGES: list = ["python", "node", "bash", "c"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### app/core/security.py
```python
from fastapi import HTTPException
from app.core.config import settings

def validate_internal_token(token: str):
    """Validate the internal authentication token"""
    if token != settings.INTERNAL_AUTH_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized access to internal API")
    
    return True
```

#### app/models/execution.py
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class ExecutionRequest(BaseModel):
    execution_id: str = Field(..., description="Unique execution ID")
    user_id: str = Field(..., description="User ID")
    code: str = Field(..., description="Code to execute")
    language: str = Field("python", description="Programming language")
    timeout: int = Field(30, description="Execution timeout in seconds")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    files: Optional[Dict[str, str]] = Field(None, description="Files to include")
    
class SessionRequest(BaseModel):
    language: str = Field("python", description="Programming language for the session")
    user_id: str = Field(..., description="User ID")
    
class ExecutionResult(BaseModel):
    output: str
    error: Optional[str] = None
    exit_code: int
    session_id: Optional[str] = None
```

#### app/services/sandbox_pool.py
```python
import asyncio
import uuid
import time
from typing import Dict, Any, List, Optional
from e2b import Sandbox
from fastapi import HTTPException

from app.core.config import settings
from app.models.execution import ExecutionRequest, SessionRequest, ExecutionResult
from app.services.language_handlers import get_language_handler

class SandboxPoolManager:
    def __init__(self):
        self.available_sandboxes: Dict[str, List[Sandbox]] = {
            lang: [] for lang in settings.SUPPORTED_LANGUAGES
        }
        self.active_sandboxes: Dict[str, Sandbox] = {}
        self.session_sandboxes: Dict[str, Sandbox] = {}
        self.user_sessions: Dict[str, List[str]] = {}
        
    async def initialize(self):
        """Initialize the sandbox pool with pre-warmed sandboxes"""
        for language in settings.SUPPORTED_LANGUAGES:
            for _ in range(settings.INITIAL_POOL_SIZE // len(settings.SUPPORTED_LANGUAGES)):
                await self._create_sandbox(language)
                
    async def _create_sandbox(self, language: str) -> Optional[Sandbox]:
        """Create a new sandbox for the specified language"""
        try:
            # Create E2B sandbox
            # Note: In production, you might want different template IDs for different languages
            # or custom templates with pre-installed packages
            sandbox = await Sandbox.create()
            
            # Add to available pool
            self.available_sandboxes[language].append(sandbox)
            
            return sandbox
        except Exception as e:
            print(f"Error creating sandbox: {str(e)}")
            return None
            
    async def _get_sandbox(self, language: str) -> Optional[Sandbox]:
        """Get a sandbox from the pool or create a new one"""
        if language not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
            
        # First try to get from available pool
        if self.available_sandboxes[language]:
            return self.available_sandboxes[language].pop(0)
            
        # If no available sandbox, try creating a new one if below max size
        if len(self.active_sandboxes) + len(self.session_sandboxes) < settings.MAX_POOL_SIZE:
            return await self._create_sandbox(language)
            
        # No sandbox available and at max capacity
        return None
        
    async def _return_sandbox(self, sandbox_id: str, reset: bool = True):
        """Return a sandbox to the pool"""
        if sandbox_id in self.active_sandboxes:
            sandbox = self.active_sandboxes.pop(sandbox_id)
            language = sandbox.metadata.get("language", "python")
            
            try:
                if reset:
                    # Reset sandbox state
                    await sandbox.process.start_command("rm -rf /tmp/* && rm -rf /home/user/*")
                    
                # Return to available pool
                self.available_sandboxes[language].append(sandbox)
            except Exception as e:
                print(f"Error returning sandbox: {str(e)}")
                await sandbox.close()
                
    async def execute_code(self, request: ExecutionRequest) -> Dict[str, Any]:
        """Execute code in a sandbox"""
        # Validate timeout
        timeout = min(request.timeout, settings.MAX_TIMEOUT)
        
        # Check if using existing session
        if request.session_id and request.session_id in self.session_sandboxes:
            sandbox = self.session_sandboxes[request.session_id]
            sandbox_id = request.session_id
        else:
            # Get sandbox from pool
            sandbox = await self._get_sandbox(request.language)
            if not sandbox:
                raise HTTPException(status_code=503, detail="No sandbox available")
                
            # Store sandbox in active sandboxes
            sandbox_id = str(uuid.uuid4())
            self.active_sandboxes[sandbox_id] = sandbox
            
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
                asyncio.create_task(self._return_sandbox(sandbox_id))
                
            return output_data
            
        except asyncio.TimeoutError:
            # Handle timeout
            if not request.session_id:
                asyncio.create_task(self._return_sandbox(sandbox_id, reset=True))
            return {"error": "Execution timed out", "output": "", "exit_code": -1}
            
        except Exception as e:
            # Handle other errors
            if not request.session_id:
                asyncio.create_task(self._return_sandbox(sandbox_id, reset=True))
            return {"error": str(e), "output": "", "exit_code": -1}
            
    async def create_session(self, request: SessionRequest) -> Dict[str, Any]:
        """Create a persistent session with a dedicated sandbox"""
        # Get sandbox from pool
        sandbox = await self._get_sandbox(request.language)
        if not sandbox:
            raise HTTPException(status_code=503, detail="No sandbox available")
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Store in session sandboxes
        self.session_sandboxes[session_id] = sandbox
        
        # Track user sessions
        if request.user_id not in self.user_sessions:
            self.user_sessions[request.user_id] = []
        self.user_sessions[request.user_id].append(session_id)
        
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
        
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a session and return the sandbox to the pool"""
        if session_id not in self.session_sandboxes:
            raise HTTPException(status_code=404, detail="Session not found")
            
        sandbox = self.session_sandboxes.pop(session_id)
        language = sandbox.metadata.get("language", "python")
        user_id = sandbox.metadata.get("user_id")
        
        # Remove from user sessions
        if user_id and user_id in self.user_sessions:
            if session_id in self.user_sessions[user_id]:
                self.user_sessions[user_id].remove(session_id)
                
        # Reset and return to pool
        try:
            await sandbox.process.start_command("rm -rf /tmp/* && rm -rf /home/user/*")
            self.available_sandboxes[language].append(sandbox)
        except Exception as e:
            print(f"Error returning session sandbox: {str(e)}")
            await sandbox.close()
            
        return {
            "success": True,
            "message": "Session ended successfully"
        }
        
    async def cleanup(self):
        """Cleanup all sandboxes when shutting down"""
        # Close all available sandboxes
        for language in self.available_sandboxes:
            for sandbox in self.available_sandboxes[language]:
                await sandbox.close()
                
        # Close all active sandboxes
        for sandbox_id in self.active_sandboxes:
            await self.active_sandboxes[sandbox_id].close()
            
        # Close all session sandboxes
        for session_id in self.session_sandboxes:
            await self.session_sandboxes[session_id].close()
```

#### app/services/language_handlers/__init__.py
```python
from typing import Dict, Any
from fastapi import HTTPException

from app.services.language_handlers.python_handler import PythonHandler
from app.services.language_handlers.node_handler import NodeHandler
from app.services.language_handlers.bash_handler import BashHandler
from app.services.language_handlers.c_handler import CHandler

# Language handler registry
_language_handlers = {
    "python": PythonHandler(),
    "node": NodeHandler(),
    "javascript": NodeHandler(),  # Alias for node
    "bash": BashHandler(),
    "shell": BashHandler(),  # Alias for bash
    "c": CHandler()
}

def get_language_handler(language: str):
    """Get the appropriate language handler for the given language"""
    if language not in _language_handlers:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {language}")
        
    return _language_handlers[language]
```

#### app/services/language_handlers/python_handler.py
```python
from typing import Dict, Any
from e2b import Sandbox
from app.models.execution import ExecutionResult

class PythonHandler:
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """Execute Python code in the sandbox"""
        # Execute Python code
        process = await sandbox.process.start_python(code=code)
        result = await process.wait()
        
        return ExecutionResult(
            output=result.stdout,
            error=result.stderr,
            exit_code=result.exit_code
        )
```

#### app/services/language_handlers/node_handler.py
```python
import tempfile
from typing import Dict, Any
from e2b import Sandbox
from app.models.execution import ExecutionResult

class NodeHandler:
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """Execute Node.js code in the sandbox"""
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
```

#### app/services/language_handlers/bash_handler.py
```python
from typing import Dict, Any
from e2b import Sandbox
from app.models.execution import ExecutionResult

class BashHandler:
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """Execute Bash commands in the sandbox"""
        # Execute bash commands
        process = await sandbox.process.start_command(code)
        result = await process.wait()
        
        return ExecutionResult(
            output=result.stdout,
            error=result.stderr,
            exit_code=result.exit_code
        )
```

#### app/services/language_handlers/c_handler.py
```python
import uuid
from typing import Dict, Any
from e2b import Sandbox
from app.models.execution import ExecutionResult

class CHandler:
    async def execute(self, sandbox: Sandbox, code: str) -> ExecutionResult:
        """Execute C code in the sandbox"""
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
```

## Deployment Instructions

### 1. Set up VPC and VMs

1. Create a VPC with appropriate subnet configuration
2. Create two VMs:
   - API Management VM: Standard VM for handling API requests
   - Xeon Execution VM: High-performance Xeon VM for running code

### 2. Configure Security

1. Set up firewall rules:
   - API Management VM: Allow inbound HTTP/HTTPS traffic
   - Xeon Execution VM: Allow only internal VPC traffic
2. Configure internal DNS or static IPs for communication between VMs
3. Set up proper authentication credentials

### 3. Deploy the API Management Service

```bash
# On the API Management VM
git clone <your-repository>
cd <repository>/api-service

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Build and run with Docker
docker build -t api-management-service .
docker run -d --name api-service -p 80:8000 -v $(pwd)/.env:/app/.env api-management-service
```

### 4. Deploy the Execution Service

```bash
# On the Xeon Execution VM
git clone <your-repository>
cd <repository>/execution-service

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Build and run with Docker
docker build -t execution-service .
docker run -d --name execution-service -p 8000:8000 -v $(pwd)/.env:/app/.env execution-service
```

### 5. Configure Monitoring and Scaling

1. Set up monitoring for resource usage and response times
2. Configure auto-scaling policies if needed
3. Implement regular log rotation and backup

## Testing the System

### Basic functionality test

```bash
# Test API endpoint
curl -X POST "http://api-vm-address/v1/code_interpreter/run" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python",
    "timeout": 30
  }'
```

### Session management test

```bash
# Create a session
curl -X POST "http://api-vm-address/v1/code_interpreter/sessions" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python"
  }'

# Use session for code execution
curl -X POST "http://api-vm-address/v1/code_interpreter/run" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from session!\")",
    "language": "python",
    "session_id": "<session_id_from_previous_response>"
  }'

# End session
curl -X DELETE "http://api-vm-address/v1/code_interpreter/sessions/<session_id>" \
  -H "Authorization: Bearer <your-token>"
```

## Conclusion

This architecture provides a secure, scalable solution for code execution that integrates with LLM systems. The separation of API management and execution concerns into different VMs enhances security while maintaining flexibility. The E2B sandbox technology provides strong isolation for executing arbitrary code while supporting multiple programming languages.