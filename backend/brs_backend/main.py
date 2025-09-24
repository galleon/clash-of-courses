"""Main FastAPI application for BRS prototype backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from brs_backend.core.config import settings
from brs_backend.core.logging import logger
from brs_backend.database.connection import engine
from brs_backend.models.database import Base
from brs_backend.agents import initialize_agents
from brs_backend.api.users import router as users_router
from brs_backend.api.requests import router as requests_router
from brs_backend.api.chat import router as chat_router
from brs_backend.api.courses import router as courses_router

# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Initialize AI agents
initialize_agents()

app = FastAPI(title="BRS Prototype API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)
app.include_router(courses_router, prefix="/api")
app.include_router(requests_router)
app.include_router(chat_router)


@app.get("/health")
def health_check():
    """Check system health and configuration status."""
    from brs_backend.agents import is_agents_available

    health_status = {
        "status": "healthy",
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "openai_model": settings.OPENAI_MODEL if settings.OPENAI_API_KEY else None,
        "database": "connected",
    }

    # Test AI service if configured
    if is_agents_available():
        health_status["openai_status"] = "working"
    elif settings.OPENAI_API_KEY:
        health_status["openai_status"] = "configured but not working"
    else:
        health_status["openai_status"] = "not configured"

    return health_status


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "BRS Prototype API", "version": "0.1.0"}
