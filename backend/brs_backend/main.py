"""Main FastAPI application for BRS prototype backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brs_backend.core.config import settings
from brs_backend.core.logging import logger
from brs_backend.database.connection import engine
from brs_backend.models.database import Base

# Import chat models to ensure tables are created
from brs_backend.api.chat_models import ChatSession, ChatMessage
from brs_backend.api.users import router as users_router
from brs_backend.api.requests import router as requests_router
from brs_backend.api.courses import router as courses_router
from brs_backend.auth.endpoints import router as auth_router
from brs_backend.api.chat_endpoints import router as chat_endpoints_router

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="BRS Prototype API", version="0.1.0")

# Add CORS middleware
# This enables the frontend (running on different ports) to communicate with the API
# Origins are configured in settings.ALLOWED_ORIGINS (see core/config.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Frontend URLs (localhost:3000, localhost:5173)
    allow_credentials=True,  # Allow cookies and Authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Allow all headers (including Authorization for JWT)
)

# Include routers with consistent /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1")  # Authentication endpoints
app.include_router(chat_endpoints_router, prefix="/api/v1")  # Chat API with SSE support
app.include_router(users_router, prefix="/api/v1")  # User management
app.include_router(courses_router, prefix="/api/v1")  # Course management
app.include_router(requests_router, prefix="/api/v1")  # Registration requests


@app.get("/health")
def health_check():
    """Check system health and configuration status."""
    health_status = {
        "status": "healthy",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "openai_model": settings.OPENAI_MODEL if settings.OPENAI_API_KEY else None,
        "database": "connected",
    }

    # Set AI status based on configuration
    if settings.OPENAI_API_KEY:
        health_status["openai_status"] = "working"
    else:
        health_status["openai_status"] = "not configured"

    return health_status


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "BRS Prototype API", "version": "0.1.0"}
