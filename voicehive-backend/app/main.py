from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.config.settings import settings
from app.routers import vapi
from app.utils.exceptions import VoiceHiveError


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    yield
    # Shutdown
    logger.info("Shutting down VoiceHive Backend")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI voice agents for enterprise call handling",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "VoiceHive Support",
        "email": "support@voicehive.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.voicehive.com",
            "description": "Production server"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(vapi.router)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with service information"""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.version,
        "status": "healthy",
        "environment": settings.environment,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
        "environment": settings.environment
    }


@app.get("/docs-info", tags=["documentation"])
async def docs_info():
    """API documentation information"""
    return {
        "swagger_ui": "/docs",
        "redoc": "/redoc",
        "openapi_json": "/openapi.json",
        "description": "VoiceHive AI Voice Agent API - Complete documentation for webhook endpoints and service integration"
    }


@app.exception_handler(VoiceHiveError)
async def voicehive_exception_handler(request, exc):
    """Handle VoiceHive custom exceptions"""
    logger.error(f"VoiceHive error: {str(exc)}")
    return {
        "error": "VoiceHive Error",
        "message": str(exc),
        "status_code": 500
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )
