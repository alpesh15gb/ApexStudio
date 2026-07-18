"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.events import lifespan
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.websocket.manager import ConnectionManager
from app.websocket.chat_handler import ChatWebSocketHandler
from app.websocket.terminal_handler import TerminalWebSocketHandler
from app.websocket.log_handler import LogWebSocketHandler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global connection manager
connection_manager = ConnectionManager()
chat_handler = ChatWebSocketHandler(connection_manager)
terminal_handler = TerminalWebSocketHandler(connection_manager)
log_handler = LogWebSocketHandler(connection_manager)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Build complete applications by chatting with AI.",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Health check
    @app.get("/api/v1/health")
    async def health_check():
        return JSONResponse(
            content={
                "status": "ok",
                "version": "0.1.0",
                "environment": settings.app_env,
            }
        )

    # Register API routers
    register_routers(app)

    # Register WebSocket routes
    register_websockets(app)

    logger.info("Application initialized successfully")
    return app


def register_routers(app: FastAPI):
    """Register all API v1 routers."""
    try:
        from app.api.v1.router import api_router
        app.include_router(api_router, prefix="/api/v1")
    except ImportError:
        logger.info("API routers not available yet")


def register_websockets(app: FastAPI):
    """Register WebSocket endpoints."""

    @app.websocket("/ws/chat/{project_id}")
    async def chat_websocket(websocket: WebSocket, project_id: str):
        user_id = "anonymous"  # TODO: Authenticate via token in query params
        await chat_handler.handle_chat(websocket, project_id, user_id)

    @app.websocket("/ws/terminal/{project_id}")
    async def terminal_websocket(websocket: WebSocket, project_id: str):
        container = websocket.query_params.get("container")
        await terminal_handler.handle_terminal(websocket, project_id, container)

    @app.websocket("/ws/logs/{project_id}")
    async def log_websocket(websocket: WebSocket, project_id: str):
        source = websocket.query_params.get("source", "all")
        await log_handler.handle_logs(websocket, project_id, source)

    logger.info("WebSocket routes registered")


app = create_app()
