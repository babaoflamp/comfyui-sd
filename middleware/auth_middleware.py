"""
Authentication middleware for ComfyUI API

Provides JWT-based token authentication for API endpoints.
Supports both header-based and query parameter authentication.

Usage:
    from middleware.auth_middleware import AuthMiddleware, require_auth

    # Add to aiohttp app
    app.middlewares.append(AuthMiddleware())

    # Protect routes
    @require_auth
    async def protected_endpoint(request):
        user_id = request['user_id']
        return web.json_response({"user": user_id})
"""

import logging
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

import jwt
from aiohttp import web

logger = logging.getLogger(__name__)


class AuthConfig:
    """Authentication configuration"""

    def __init__(self, secret_key: Optional[str] = None,
                 algorithm: str = "HS256",
                 token_expiry_hours: int = 24,
                 require_auth: bool = False):
        """
        Initialize authentication config

        Args:
            secret_key: JWT secret key (auto-generated if None)
            algorithm: JWT algorithm (default: HS256)
            token_expiry_hours: Token expiry time in hours
            require_auth: Whether to require auth globally
        """
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.token_expiry_hours = token_expiry_hours
        self.require_auth = require_auth
        self.users: Dict[str, Dict[str, Any]] = {}

        # Log secret key for development (NEVER in production)
        logger.warning(f"JWT Secret Key: {self.secret_key}")


class AuthManager:
    """Manages authentication tokens and users"""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def generate_token(self, user_id: str, **kwargs) -> str:
        """
        Generate JWT token

        Args:
            user_id: User identifier
            **kwargs: Additional claims

        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.config.token_expiry_hours),
            **kwargs
        }

        token = jwt.encode(
            payload,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )

        # Store token metadata
        self.tokens[token] = {
            'user_id': user_id,
            'created': datetime.utcnow().isoformat(),
            'expires': payload['exp'].isoformat()
        }

        logger.info(f"Token generated for user: {user_id}")
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning(f"Token expired: {token[:20]}...")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False


class AuthMiddleware:
    """AIOHTTP middleware for authentication"""

    def __init__(self, config: Optional[AuthConfig] = None,
                 public_paths: Optional[list] = None):
        """
        Initialize middleware

        Args:
            config: AuthConfig instance
            public_paths: List of paths that don't require auth
        """
        self.config = config or AuthConfig()
        self.auth_manager = AuthManager(self.config)
        self.public_paths = public_paths or [
            '/health',
            '/api/auth/login',
            '/api/auth/token',
            '/',
        ]

    @web.middleware
    async def middleware_handler(self, request: web.Request,
                                  handler) -> web.Response:
        """
        Middleware handler

        Extracts authentication from:
        1. Authorization header (Bearer token)
        2. X-API-Key header (API key)
        3. api_token query parameter
        """

        # Skip auth for public paths
        if any(request.path.startswith(path) for path in self.public_paths):
            return await handler(request)

        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        elif 'X-API-Key' in request.headers:
            # For simple API key auth
            token = request.headers.get('X-API-Key')
        else:
            # Try query parameter
            token = request.query.get('api_token')

        # Verify token if required
        if self.config.require_auth or request.path.startswith('/api/'):
            if not token:
                return web.json_response(
                    {'error': 'Unauthorized', 'message': 'Missing authentication token'},
                    status=401
                )

            payload = self.auth_manager.verify_token(token)
            if not payload:
                return web.json_response(
                    {'error': 'Unauthorized', 'message': 'Invalid or expired token'},
                    status=401
                )

            # Store user info in request
            request['user_id'] = payload.get('user_id')
            request['auth_payload'] = payload

        # Call handler
        return await handler(request)

    def generate_token(self, user_id: str, **kwargs) -> str:
        """Generate token for user"""
        return self.auth_manager.generate_token(user_id, **kwargs)

    def revoke_token(self, token: str) -> bool:
        """Revoke token"""
        return self.auth_manager.revoke_token(token)


def require_auth(f):
    """
    Decorator for protecting routes

    Usage:
        @require_auth
        async def my_endpoint(request):
            user_id = request.get('user_id')
            return web.json_response({'user': user_id})
    """
    @wraps(f)
    async def decorated(request, *args, **kwargs):
        if 'user_id' not in request:
            return web.json_response(
                {'error': 'Unauthorized', 'message': 'Authentication required'},
                status=401
            )
        return await f(request, *args, **kwargs)
    return decorated


# Example auth routes
async def handle_login(request):
    """
    Login endpoint

    POST /api/auth/login
    {
        "username": "user@example.com",
        "password": "password"
    }
    """
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return web.json_response(
                {'error': 'Invalid credentials'},
                status=400
            )

        # TODO: Implement actual user verification
        # For now, accept any credentials
        auth_manager = request.app.get('auth_manager')
        token = auth_manager.generate_token(username)

        return web.json_response({
            'token': token,
            'user_id': username,
            'token_type': 'Bearer'
        })

    except json.JSONDecodeError:
        return web.json_response(
            {'error': 'Invalid JSON'},
            status=400
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


async def handle_refresh_token(request):
    """
    Refresh token endpoint

    POST /api/auth/refresh
    {
        "token": "current_token"
    }
    """
    try:
        data = await request.json()
        old_token = data.get('token')

        if not old_token:
            return web.json_response(
                {'error': 'Token required'},
                status=400
            )

        auth_manager = request.app.get('auth_manager')
        payload = auth_manager.verify_token(old_token)

        if not payload:
            return web.json_response(
                {'error': 'Invalid or expired token'},
                status=401
            )

        # Generate new token
        user_id = payload.get('user_id')
        new_token = auth_manager.generate_token(user_id)

        # Optionally revoke old token
        auth_manager.revoke_token(old_token)

        return web.json_response({
            'token': new_token,
            'user_id': user_id,
            'token_type': 'Bearer'
        })

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


async def handle_logout(request):
    """
    Logout endpoint

    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'Invalid authorization header'},
                status=400
            )

        token = auth_header[7:]
        auth_manager = request.app.get('auth_manager')
        auth_manager.revoke_token(token)

        logger.info(f"User {request.get('user_id')} logged out")
        return web.json_response({'message': 'Logged out successfully'})

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return web.json_response(
            {'error': 'Internal server error'},
            status=500
        )


def setup_auth_routes(app: web.Application, auth_middleware: AuthMiddleware):
    """
    Setup authentication routes

    Args:
        app: AIOHTTP application
        auth_middleware: AuthMiddleware instance
    """
    app.router.add_post('/api/auth/login', handle_login)
    app.router.add_post('/api/auth/refresh', handle_refresh_token)
    app.router.add_post('/api/auth/logout', handle_logout)

    # Store auth manager in app for route handlers
    app['auth_manager'] = auth_middleware.auth_manager
