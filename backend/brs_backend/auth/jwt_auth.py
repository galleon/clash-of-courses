"""
Simple JWT authentication for BRS Chat API
"""

import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import HTTPException, status, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from brs_backend.database.connection import get_db
from brs_backend.models.database import (
    User,
    Student,
    Instructor,
    DepartmentHead,
    SystemAdmin,
)

# Simple password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
SECRET_KEY = "brs_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Demo password for all users (in production, store hashed passwords in database)
DEMO_PASSWORD = "password123"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(
    username: str, password: str, db: Session = None
) -> dict | None:
    """Authenticate user against database records."""
    if not db:
        from brs_backend.database.connection import get_db

        db = next(get_db())

    # For demo purposes, use simple password check
    # In production, store bcrypt hashed passwords in User table
    if password not in ["password123", "advisor123", "head123", "admin123"]:
        return None

    # Query with polymorphic loading to get the specific user type
    user = db.query(User).filter(User.username == username, User.is_active == 1).first()
    if not user:
        return None

    # Determine the correct actor_id based on user type
    if user.user_type == "student" and user.student_id:
        actor_id = str(user.student_id)
    elif user.user_type == "instructor" and user.instructor_id:
        actor_id = str(user.instructor_id)
    elif user.user_type == "department_head" and user.department_head_id:
        actor_id = str(user.department_head_id)
    elif user.user_type == "system_admin" and user.admin_id:
        actor_id = str(user.admin_id)
    else:
        actor_id = str(user.user_id)  # Fallback to user_id

    return {
        "username": user.username,
        "full_name": user.full_name,
        "user_type": user.user_type,
        "user_id": str(user.user_id),
        "actor_id": actor_id,  # This is the specific entity ID for the user's role
        "email": user.email,
        # Include specific entity ID if available
        "entity_id": str(
            user.student_id
            or user.instructor_id
            or user.department_head_id
            or user.admin_id
            or user.user_id
        ),
    }


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = None, db: Session = Depends(get_db)) -> dict:
    """Get current user from JWT token - with database backing"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        # Get user from database with polymorphic loading
        user = (
            db.query(User)
            .filter(User.username == username, User.is_active == 1)
            .first()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "user_type": user.user_type,
            "full_name": user.full_name,
            "actor_id": str(user.user_id),
            "email": user.email,
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
