"""
OpenAPI/Swagger specification generator for ComfyUI API

Generates OpenAPI 3.0 specification for API documentation.
Supports Swagger UI and ReDoc integration.

Usage:
    from api_server.openapi_spec import get_openapi_spec, setup_openapi_routes

    # Generate OpenAPI spec
    spec = get_openapi_spec()

    # Add routes for documentation
    setup_openapi_routes(app)
"""

import logging
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)


def get_openapi_spec(
    title: str = "ComfyUI API",
    version: str = "0.3.67",
    description: str = "Visual AI engine for Stable Diffusion workflows",
    base_url: str = "http://localhost:8188"
) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification

    Returns:
        OpenAPI specification dictionary
    """

    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": version,
            "description": description,
            "contact": {
                "name": "ComfyUI Project",
                "url": "https://github.com/comfyanonymous/ComfyUI",
                "email": "support@comfy.org"
            },
            "license": {
                "name": "GPL-3.0",
                "url": "https://www.gnu.org/licenses/gpl-3.0.html"
            }
        },
        "servers": [
            {
                "url": base_url,
                "description": "Development server"
            }
        ],
        "paths": {
            # Authentication endpoints
            "/api/auth/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User login",
                    "description": "Authenticate user and get JWT token",
                    "operationId": "loginUser",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {
                                            "type": "string",
                                            "example": "user@example.com"
                                        },
                                        "password": {
                                            "type": "string",
                                            "format": "password",
                                            "example": "password123"
                                        }
                                    },
                                    "required": ["username", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "token": {
                                                "type": "string",
                                                "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                                            },
                                            "user_id": {
                                                "type": "string"
                                            },
                                            "token_type": {
                                                "type": "string",
                                                "example": "Bearer"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid credentials"
                        }
                    }
                }
            },

            "/api/auth/logout": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "User logout",
                    "description": "Logout user and revoke token",
                    "operationId": "logoutUser",
                    "security": [
                        {"bearerAuth": []}
                    ],
                    "responses": {
                        "200": {
                            "description": "Logout successful"
                        },
                        "401": {
                            "description": "Unauthorized"
                        }
                    }
                }
            },

            # Workflow endpoints
            "/prompt": {
                "post": {
                    "tags": ["Workflows"],
                    "summary": "Submit workflow",
                    "description": "Submit a workflow to the execution queue",
                    "operationId": "submitWorkflow",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {
                                            "type": "object",
                                            "description": "Graph of nodes to execute",
                                            "additionalProperties": {
                                                "type": "object",
                                                "properties": {
                                                    "class_type": {"type": "string"},
                                                    "inputs": {"type": "object"}
                                                },
                                                "required": ["class_type", "inputs"]
                                            }
                                        }
                                    },
                                    "required": ["prompt"]
                                },
                                "example": {
                                    "prompt": {
                                        "1": {
                                            "class_type": "CheckpointLoaderSimple",
                                            "inputs": {
                                                "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Workflow submitted",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "prompt_id": {"type": "string"},
                                            "number": {"type": "integer"},
                                            "node_errors": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["Workflows"],
                    "summary": "Get queue status",
                    "description": "Get current execution queue status",
                    "operationId": "getQueueStatus",
                    "responses": {
                        "200": {
                            "description": "Queue status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "exec_info": {
                                                "type": "object",
                                                "properties": {
                                                    "queue_remaining": {"type": "integer"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },

            "/history": {
                "get": {
                    "tags": ["Workflows"],
                    "summary": "Get execution history",
                    "description": "Get history of executed workflows",
                    "operationId": "getHistory",
                    "responses": {
                        "200": {
                            "description": "Execution history",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "additionalProperties": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },

            # System endpoints
            "/api/nodes": {
                "get": {
                    "tags": ["System"],
                    "summary": "Get available nodes",
                    "description": "Get list of available nodes and their specifications",
                    "operationId": "getNodes",
                    "responses": {
                        "200": {
                            "description": "Available nodes",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "additionalProperties": {
                                            "type": "object"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },

            "/api/models": {
                "get": {
                    "tags": ["System"],
                    "summary": "Get available models",
                    "description": "Get list of available model checkpoints",
                    "operationId": "getModels",
                    "responses": {
                        "200": {
                            "description": "Available models",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    }
                }
            },

            "/health": {
                "get": {
                    "tags": ["System"],
                    "summary": "Health check",
                    "description": "Check if server is running",
                    "operationId": "healthCheck",
                    "responses": {
                        "200": {
                            "description": "Server is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                },
                "apiKey": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                        "details": {"type": "string"}
                    }
                },
                "Node": {
                    "type": "object",
                    "properties": {
                        "class_type": {"type": "string"},
                        "display_name": {"type": "string"},
                        "category": {"type": "string"},
                        "input_types": {"type": "object"},
                        "return_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "WorkflowPrompt": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "class_type": {"type": "string"},
                            "inputs": {"type": "object"}
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "Authentication",
                "description": "User authentication and token management"
            },
            {
                "name": "Workflows",
                "description": "Workflow execution and management"
            },
            {
                "name": "System",
                "description": "System information and node management"
            }
        ]
    }

    return spec


def get_swagger_ui_html(spec_url: str = "/api/openapi.json") -> str:
    """
    Generate Swagger UI HTML

    Args:
        spec_url: URL to OpenAPI specification

    Returns:
        HTML string for Swagger UI
    """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ComfyUI API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.js"></script>
        <script>
            SwaggerUIBundle({{
                url: '{spec_url}',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: 'BaseLayout'
            }})
        </script>
    </body>
    </html>
    """


def get_redoc_html(spec_url: str = "/api/openapi.json") -> str:
    """
    Generate ReDoc HTML

    Args:
        spec_url: URL to OpenAPI specification

    Returns:
        HTML string for ReDoc
    """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ComfyUI API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url='{spec_url}'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """


def setup_openapi_routes(app):
    """
    Setup OpenAPI documentation routes

    Args:
        app: AIOHTTP application
    """
    from aiohttp import web

    spec = get_openapi_spec()

    # OpenAPI specification endpoint
    async def openapi_json(request):
        return web.json_response(spec)

    # Swagger UI
    async def swagger_ui(request):
        html = get_swagger_ui_html()
        return web.Response(text=html, content_type='text/html')

    # ReDoc
    async def redoc_ui(request):
        html = get_redoc_html()
        return web.Response(text=html, content_type='text/html')

    # Health check
    async def health_check(request):
        return web.json_response({"status": "healthy"})

    # Add routes
    app.router.add_get('/api/openapi.json', openapi_json)
    app.router.add_get('/api/docs', swagger_ui)
    app.router.add_get('/api/redoc', redoc_ui)
    app.router.add_get('/health', health_check)

    logger.info("OpenAPI documentation routes registered")
    logger.info("  - Swagger UI: /api/docs")
    logger.info("  - ReDoc: /api/redoc")
    logger.info("  - OpenAPI JSON: /api/openapi.json")
