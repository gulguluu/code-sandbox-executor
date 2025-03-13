# E2B Code Execution Environment for LLM Integration

A secure, scalable code execution service that integrates with LLMs using E2B sandboxes. This system allows for isolated execution of code in multiple programming languages.

## Supported Languages

The system currently supports the following programming languages:

1. **Python**: Execute Python code directly
2. **JavaScript/Node.js**: Execute JavaScript code using Node.js
3. **Bash/Shell**: Execute shell commands and scripts
4. **C**: Compile and execute C code

## Architecture

The system consists of two main components:

1. **API Service**: Handles external requests, authentication, and API compatibility
2. **Execution Service**: Manages E2B sandboxes and executes code in isolated environments

```bash
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
## Getting Started

### Prerequisites

- Docker and Docker Compose
- E2B API key (for production use)

### Running the Services

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd coding_agent_executor_ws
   ```

2. Configure environment variables:
   - For production, edit the environment variables in `docker-compose.yml`
   - Make sure to change the security tokens and keys

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. The API service will be available at `http://localhost:8000`

## API Usage

### Authentication

The API uses JWT token-based authentication. To get a token, you need to authenticate with valid credentials.

### Code Execution

To execute code, send a POST request to the `/v1/code_interpreter/run` endpoint:

```bash
curl -X POST "http://localhost:8000/v1/code_interpreter/run" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python",
    "timeout": 30
  }'
```

### Session Management

For stateful execution, you can create a session:

```bash
# Create a session
curl -X POST "http://localhost:8000/v1/code_interpreter/sessions" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python"
  }'

# Use session for code execution
curl -X POST "http://localhost:8000/v1/code_interpreter/run" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from session!\")",
    "language": "python",
    "session_id": "<session_id_from_previous_response>"
  }'

# End session
curl -X DELETE "http://localhost:8000/v1/code_interpreter/sessions/<session_id>" \
  -H "Authorization: Bearer <your-token>"
```

## Development

### Project Structure

```
/
├── api_service/               # API service
│   ├── app/
│   │   ├── core/              # Core functionality
│   │   ├── models/            # Data models
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Service clients
│   │   └── main.py            # Entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── execution_service/         # Execution service
│   ├── app/
│   │   ├── core/              # Core functionality
│   │   ├── models/            # Data models
│   │   ├── services/          # Service implementations
│   │   │   └── language_handlers/  # Language-specific handlers
│   │   ├── utils/             # Utilities
│   │   └── main.py            # Entry point
│   ├── Dockerfile
│   └── requirements.txt
│
└── docker-compose.yml         # Docker Compose configuration
```

### Adding a New Language

To add support for a new programming language:

1. Create a new handler in `execution_service/app/services/language_handlers/`
2. Implement the `execute` method that conforms to the `LanguageHandler` protocol
3. Register the handler in `execution_service/app/services/language_handlers/__init__.py`
4. Add the language to the `SUPPORTED_LANGUAGES` list in the configuration

## Security Considerations

- The execution service is isolated and only accessible from the API service
- Code is executed in isolated E2B sandboxes
- Resource limits are enforced to prevent abuse
- Authentication and authorization are required for all API endpoints

## Production Deployment

For production deployment:

1. Use secure, randomly generated tokens for `SECRET_KEY` and `INTERNAL_AUTH_TOKEN`
2. Configure proper CORS settings
3. Set up HTTPS with a valid SSL certificate
4. Configure resource limits appropriate for your hardware
5. Set up monitoring and logging
6. Consider using a container orchestration system like Kubernetes

## License

[MIT License](LICENSE)
