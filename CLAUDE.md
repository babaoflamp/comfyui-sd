# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **ComfyUI integration project** that adds enterprise-grade features to ComfyUI through custom middleware and utilities. The project provides:

1. **JWT Authentication** - Token-based API authentication
2. **API Documentation** - OpenAPI/Swagger specification generation
3. **Enhanced Logging** - Structured JSON logging with rotation

This is **NOT** the main ComfyUI repository. This is a wrapper/integration layer that should be used alongside ComfyUI.

### Key Technologies
- **Python 3.9+** - Core implementation
- **aiohttp** - Async web framework (ComfyUI's server framework)
- **PyJWT** - JWT token generation and validation
- **SQLAlchemy + Alembic** - Database ORM and migrations
- **Pydantic ~2.0** - Data validation

## Repository Structure

```
.
├── api_server/
│   └── openapi_spec.py          # OpenAPI 3.0 specification generator
├── app/
│   └── enhanced_logger.py       # Structured logging with JSON output
├── middleware/
│   └── auth_middleware.py       # JWT authentication middleware
├── web/                         # Git submodule: ComfyUI_frontend
├── requirements.txt             # Python dependencies
└── pyproject.toml              # Project metadata and tool config
```

## Common Development Commands

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for auth
pip install PyJWT
```

### Code Quality

```bash
# Linting (ruff is configured in pyproject.toml)
ruff check .

# Auto-fix issues
ruff check . --fix

# Check specific rules
ruff check . --select E,F,W  # PEP 8 + Pyflakes
ruff check . --select T      # Print statement detection
```

### Testing

Currently no automated tests exist. When adding tests:

```bash
# Install pytest
pip install pytest pytest-asyncio pytest-aiohttp

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

## Module Documentation

### 1. Authentication Middleware (`middleware/auth_middleware.py`)

JWT-based authentication for aiohttp applications.

**Key Components:**
- `AuthConfig` - Configuration for authentication settings
- `AuthManager` - Token generation and validation
- `AuthMiddleware` - aiohttp middleware for request authentication
- `setup_auth_routes()` - Adds `/api/auth/login` and `/api/auth/logout` endpoints
- `@require_auth` decorator - Protects individual route handlers

**Integration Example:**
```python
from aiohttp import web
from middleware.auth_middleware import AuthMiddleware, setup_auth_routes

app = web.Application()

# Initialize auth middleware
auth = AuthMiddleware(
    public_paths=['/health', '/api/auth/login']
)
app.middlewares.append(auth.middleware_handler)

# Add auth routes
setup_auth_routes(app, auth)
```

**Usage:**
```bash
# Login
curl -X POST http://localhost:8188/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl http://localhost:8188/api/protected \
  -H "Authorization: Bearer <token>"
```

### 2. OpenAPI Specification (`api_server/openapi_spec.py`)

Generates OpenAPI 3.0 documentation for the API.

**Key Functions:**
- `get_openapi_spec()` - Returns OpenAPI spec dictionary
- `setup_openapi_routes()` - Adds `/api/docs`, `/api/redoc`, `/api/openapi.json`

**Integration Example:**
```python
from api_server.openapi_spec import setup_openapi_routes

# Add documentation routes
setup_openapi_routes(app)

# Access:
# - Swagger UI: http://localhost:8188/api/docs
# - ReDoc:      http://localhost:8188/api/redoc
# - JSON spec:  http://localhost:8188/api/openapi.json
```

### 3. Enhanced Logger (`app/enhanced_logger.py`)

Structured logging with JSON output and file rotation.

**Key Components:**
- `JSONFormatter` - Formats logs as JSON
- `ColoredFormatter` - Colored console output
- `setup_enhanced_logger()` - Configures logger with multiple handlers
- `LogContext` - Context manager for operation tracking
- `MetricsLogger` - Performance metrics tracking

**Usage Example:**
```python
from app.enhanced_logger import setup_enhanced_logger
import logging

logger = setup_enhanced_logger(
    name="myapp",
    level=logging.INFO,
    log_file="/var/log/myapp/app.log",
    json_output=True
)

logger.info("Server started", extra={
    "port": 8188,
    "mode": "production"
})
```

## Integration with ComfyUI

To integrate these modules with a ComfyUI installation:

1. **Install ComfyUI separately** or add as submodule
2. **Import and use these modules** in ComfyUI's `server.py`
3. **Configure authentication** to protect API endpoints
4. **Add API documentation** for custom nodes

Example integration in ComfyUI's server:

```python
# In ComfyUI's server.py
from middleware.auth_middleware import AuthMiddleware, setup_auth_routes
from api_server.openapi_spec import setup_openapi_routes
from app.enhanced_logger import setup_enhanced_logger

# Setup logging
logger = setup_enhanced_logger("comfyui")

# Add authentication
auth = AuthMiddleware(public_paths=['/'])
app.middlewares.append(auth.middleware_handler)
setup_auth_routes(app, auth)

# Add API documentation
setup_openapi_routes(app)
```

## Development Patterns

### Async/Await
All aiohttp handlers must be async:
```python
async def my_handler(request):
    return web.json_response({"status": "ok"})
```

### Error Handling
Return proper HTTP status codes:
```python
try:
    result = await process_request(request)
    return web.json_response(result)
except ValueError as e:
    return web.json_response(
        {"error": str(e)},
        status=400
    )
except Exception as e:
    logger.error("Unexpected error", exc_info=True)
    return web.json_response(
        {"error": "Internal server error"},
        status=500
    )
```

### Logging Best Practices
Use structured logging instead of print statements:
```python
# Bad
print(f"User {user_id} logged in")

# Good
logger.info("User logged in", extra={"user_id": user_id})
```

## Security Considerations

### Authentication
- **Secret Key**: Set via environment variable in production
- **Token Expiry**: Configure appropriate expiry times (default: 24 hours)
- **HTTPS**: Always use HTTPS in production
- **Password Hashing**: Implement proper password hashing (not included in current implementation)

### API Security
- **CORS**: Configure CORS policies appropriately
- **Rate Limiting**: Add rate limiting for public endpoints
- **Input Validation**: Validate all user inputs
- **SQL Injection**: Use parameterized queries with SQLAlchemy

## Configuration

### Environment Variables
Recommended environment variables for production:

```bash
# Authentication
AUTH_SECRET_KEY=<secure-random-key>
AUTH_TOKEN_EXPIRY_HOURS=24
AUTH_REQUIRE_AUTH=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/comfyui/app.log
LOG_JSON_OUTPUT=true

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8188
```

### pyproject.toml
Ruff linting is configured with rules:
- `E`, `F`, `W` - PEP 8 errors, Pyflakes, warnings
- `N805` - Invalid method argument names
- `S307`, `S102` - Security warnings for eval/exec
- `T` - Print statement detection

Pylint has many rules disabled for flexibility. See `pyproject.toml` for full list.

## Dependencies

### Core Dependencies
- `aiohttp>=3.10.0,<3.11.0` - Web framework
- `PyJWT` - JWT token handling
- `pydantic~=2.0` - Data validation
- `SQLAlchemy` - Database ORM
- `alembic` - Database migrations

### Optional Dependencies
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-aiohttp` - aiohttp test utilities
- `ruff` - Linting and formatting

## Git Workflow

- **Main Branch**: `master`
- **Submodules**: ComfyUI_frontend in `web/` directory

### Submodule Management
```bash
# Initialize submodules
git submodule update --init --recursive

# Update submodules
git submodule update --remote

# Pull with submodules
git pull --recurse-submodules
```

## Future Enhancements

Potential improvements to consider:

1. **Database Integration**
   - User management tables
   - Session storage
   - Audit logging

2. **Additional Middleware**
   - Rate limiting
   - Request caching
   - CORS handling

3. **Testing**
   - Unit tests for each module
   - Integration tests with aiohttp
   - Security testing

4. **Monitoring**
   - Prometheus metrics
   - Health check endpoints
   - Performance dashboards

## Related Projects

- **ComfyUI Core**: https://github.com/comfyanonymous/ComfyUI
- **ComfyUI Frontend**: https://github.com/Comfy-Org/ComfyUI_frontend
- **ComfyUI Desktop**: https://github.com/Comfy-Org/desktop

## Documentation

For ComfyUI-specific documentation, see:
- https://docs.comfy.org/
- https://github.com/comfyanonymous/ComfyUI/wiki

For module-specific implementation details, see:
- `IMPLEMENTATION_GUIDE.md` - Detailed integration instructions
- `PROJECT_ANALYSIS.md` - Project analysis and architecture
