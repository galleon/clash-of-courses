"""Core configuration and settings for the BRS backend."""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Logging configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        self.ENABLE_DETAILED_LOGGING = (
            os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
        )

        # AI service configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL")

        # Database configuration
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@db:5432/brs_prototype_db"
        )

        # API configuration
        self.API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

        # CORS configuration - Frontend Origins
        # These URLs are allowed to make requests to the API from browsers
        self.ALLOWED_ORIGINS = [
            "http://localhost:3000",  # Production frontend (serve -s dist)
            "http://localhost:5173",  # Development frontend (Vite dev server)
        ]
        # Note: In production, replace with actual domain(s) like "https://yourdomain.com"
        # Never use ["*"] with allow_credentials=True in production

        # Development settings
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# Global settings instance
settings = Settings()
