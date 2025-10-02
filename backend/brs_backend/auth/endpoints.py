"""
Authentication endpoints for BRS
"""

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from ..auth.jwt_auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return JWT token"""
    logger.info(f"🔐 LOGIN ATTEMPT: username='{credentials.username}'")

    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        logger.warning(
            f"❌ LOGIN FAILED: Invalid credentials for username='{credentials.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        f"✅ LOGIN SUCCESS: username='{credentials.username}', user_type='{user['user_type']}'"
    )

    # Create JWT token with user info
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user["username"],
        "full_name": user["full_name"],
        "user_type": user["user_type"],  # Changed from role to user_type
        "actor_id": user["actor_id"],
    }
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        user={
            "username": user["username"],
            "full_name": user["full_name"],
            "user_type": user["user_type"],  # Changed from role to user_type
            "actor_id": user["actor_id"],
        },
    )
