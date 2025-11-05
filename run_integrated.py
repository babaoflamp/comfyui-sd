#!/usr/bin/env python3
"""
ComfyUI Enterprise Integration Runner

This script integrates enterprise features (authentication, API docs, enhanced logging)
with ComfyUI and runs the integrated server.
"""

import sys
import os
import logging
from pathlib import Path

# Add ComfyUI to path
COMFYUI_PATH = Path(__file__).parent / "ComfyUI"
sys.path.insert(0, str(COMFYUI_PATH))

# Import our enterprise modules
from middleware.auth_middleware import AuthMiddleware, AuthConfig, setup_auth_routes
from api_server.openapi_spec import setup_openapi_routes
from app.enhanced_logger import setup_enhanced_logger

# Setup enhanced logging
logger = setup_enhanced_logger(
    name="comfyui-enterprise",
    level=logging.INFO,
    log_file=None,  # Console only for now
    json_output=False,  # Human-readable format
    use_colors=True
)

logger.info("Starting ComfyUI with Enterprise Features")
logger.info(f"ComfyUI path: {COMFYUI_PATH}")

# Import ComfyUI's main modules
try:
    import execution
    import folder_paths
    import server
    from aiohttp import web
    logger.info("ComfyUI modules imported successfully")
except ImportError as e:
    logger.error(f"Failed to import ComfyUI modules: {e}")
    logger.error("Make sure ComfyUI is installed in the ComfyUI/ directory")
    sys.exit(1)

# Configure authentication
auth_config = AuthConfig(
    secret_key=os.getenv('AUTH_SECRET_KEY', 'dev-secret-key-change-in-production'),
    algorithm="HS256",
    token_expiry_hours=int(os.getenv('AUTH_TOKEN_EXPIRY_HOURS', '24')),
    require_auth=os.getenv('AUTH_REQUIRE_AUTH', 'false').lower() == 'true'
)

logger.info(f"Authentication configured (require_auth: {auth_config.require_auth})")

# Get the existing aiohttp app from ComfyUI server
def integrate_enterprise_features(app):
    """
    Integrate our enterprise features into ComfyUI's aiohttp app
    """
    logger.info("Integrating enterprise features...")

    # Add authentication middleware
    public_paths = [
        '/',
        '/api/auth/login',
        '/api/auth/logout',
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
        '/ws',  # WebSocket endpoint
        '/view',  # Image view endpoint
        '/upload',  # Upload endpoint
    ]

    auth = AuthMiddleware(
        config=auth_config,
        public_paths=public_paths
    )

    # Insert auth middleware at the beginning
    app.middlewares.insert(0, auth.middleware_handler)
    logger.info(f"Authentication middleware added (public paths: {len(public_paths)})")

    # Setup authentication routes
    setup_auth_routes(app, auth)
    logger.info("Authentication routes configured (/api/auth/login, /api/auth/logout)")

    # Setup API documentation
    setup_openapi_routes(app)
    logger.info("API documentation routes configured (/api/docs, /api/redoc)")

    logger.info("Enterprise features integrated successfully!")
    logger.info("")
    logger.info("=" * 60)
    logger.info("ComfyUI Enterprise Edition Ready!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Available endpoints:")
    logger.info("  - ComfyUI Interface: http://localhost:8188/")
    logger.info("  - API Swagger Docs:  http://localhost:8188/api/docs")
    logger.info("  - API ReDoc:         http://localhost:8188/api/redoc")
    logger.info("  - Login Endpoint:    http://localhost:8188/api/auth/login")
    logger.info("")
    if not auth_config.require_auth:
        logger.info("Authentication: OPTIONAL (set AUTH_REQUIRE_AUTH=true to enforce)")
    else:
        logger.info("Authentication: REQUIRED")
    logger.info("")
    logger.info("=" * 60)

if __name__ == "__main__":
    # Change to ComfyUI directory to ensure relative paths work
    os.chdir(COMFYUI_PATH)

    # Import and run ComfyUI's main
    try:
        # ComfyUI creates the app in server module
        # We need to hook into it after creation but before running

        import importlib.util
        spec = importlib.util.spec_from_file_location("comfyui_main", str(COMFYUI_PATH / "main.py"))
        comfyui_main = importlib.util.module_from_spec(spec)

        # Execute ComfyUI's main to set everything up
        logger.info("Initializing ComfyUI...")
        spec.loader.exec_module(comfyui_main)

        # Get the app from server module
        if hasattr(server, 'app'):
            app = server.app
            integrate_enterprise_features(app)

        # If ComfyUI's main doesn't start the server, we start it here
        # (Usually ComfyUI's main.py starts the server automatically)

    except Exception as e:
        logger.error(f"Error running ComfyUI: {e}", exc_info=True)
        sys.exit(1)
