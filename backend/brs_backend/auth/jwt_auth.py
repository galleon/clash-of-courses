"""
Simple JWT authentication for BRS Chat API
"""

import jwt
from datetime import datetime, timedelta, UTC
from typing import Optional
from fastapi import HTTPException, status
from passlib.context import CryptContext

# Simple password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
SECRET_KEY = "brs_secret_key_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Demo user data (in production, this would be in database)
DEMO_USERS = {
    "sarah.ahmed": {
        "username": "sarah.ahmed",
        "password": "password123",
        "full_name": "Sarah Ahmed",
        "role": "student",
        "actor_id": "student_sarah_ahmed",
    },
    "marcus.thompson": {
        "username": "marcus.thompson",
        "password": "password123",
        "full_name": "Marcus Thompson",
        "role": "student",
        "actor_id": "student_marcus_thompson",
    },
    "emily.chen": {
        "username": "emily.chen",
        "password": "password123",
        "full_name": "Emily Chen",
        "role": "student",
        "actor_id": "student_emily_chen",
    },
    "dr.rodriguez": {
        "username": "dr.rodriguez",
        "password": "advisor123",
        "full_name": "Dr. Maria Rodriguez",
        "role": "advisor",
        "actor_id": "advisor_dr_rodriguez",
    },
    "prof.kim": {
        "username": "prof.kim",
        "password": "advisor123",
        "full_name": "Prof. David Kim",
        "role": "advisor",
        "actor_id": "advisor_prof_kim",
    },
    "dr.johnson": {
        "username": "dr.johnson",
        "password": "head123",
        "full_name": "Dr. Jennifer Johnson",
        "role": "department_head",
        "actor_id": "head_dr_johnson",
    },
    "admin.user": {
        "username": "admin.user",
        "password": "admin123",
        "full_name": "System Admin",
        "role": "system_admin",
        "actor_id": "admin_system",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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


def get_current_user(token: str = None) -> dict:
    """Get current user from JWT token - for SmolAgents compatibility"""
    if not token:
        # For testing purposes, return a mock student user
        return {
            "user_id": "student_sarah_ahmed",
            "username": "sarah.ahmed", 
            "role": "student",
            "full_name": "Sarah Ahmed"
        }
    
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
        # Get user from demo users
        user_data = DEMO_USERS.get(username)
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {
            "user_id": user_data["actor_id"],
            "username": user_data["username"],
            "role": user_data["role"],
            "full_name": user_data["full_name"]
        }
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
