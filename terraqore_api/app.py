"""
FastAPI Application Factory
Main entry point for TerraQore API service.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from terraqore_api.routers import self_marketing_agent

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI app instance.
    """
    app = FastAPI(
        title="TerraQore API",
        description="Personal Developer Assistant for Agentic AI Projects",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
    )
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "terraqore-api",
            "version": "0.1.0"
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """API root endpoint."""
        return {
            "message": "Welcome to TerraQore API",
            "docs": "/api/docs",
            "version": "0.1.0"
        }
    
    # Global error handler
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": type(exc).__name__
            }
        )
    
    # Include routers
    from terraqore_api.routers import projects, tasks, workflows, metrics, websocket
    
    app.include_router(
        projects.router,
        prefix="/api/projects",
        tags=["projects"]
    )
    
    app.include_router(
        tasks.router,
        prefix="/api/tasks",
        tags=["tasks"]
    )
    
    app.include_router(
        workflows.router,
        prefix="/api/workflows",
        tags=["workflows"]
    )
    
    app.include_router(
        metrics.router,
        tags=["metrics"]
    )
    
    app.include_router(
        websocket.router,
        tags=["websocket"]
    )
    
    app.include_router(
        self_marketing_agent.router,
        tags=["task6-marketing"]
    )
    
    logger.info("FastAPI application initialized successfully")
    return app


if __name__ == "__main__":
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
