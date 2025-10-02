"""JWT Authentication Handler for BRS."""

import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel

# In production, use environment variables or secret management
JWT_SECRET = "your-super-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


class JWTClaims(BaseModel):
    """JWT claims structure for BRS authentication."""

    sub: str  # subject (user ID)
    role: str  # student, advisor, department_head, registrar
    actor_id: str  # UUID of the actor (student_id, etc.)
    full_name: str
    email: str | None = None
    department_id: str | None = None
    program_id: str | None = None
    iat: int  # issued at
    exp: int  # expires at
    jti: str  # JWT ID for revocation


def create_jwt_token(
    user_id: str,
    role: str,
    actor_id: str,
    full_name: str,
    email: str | None = None,
    department_id: str | None = None,
    program_id: str | None = None,
) -> str:
    """Create a JWT token with the specified claims."""
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    claims = JWTClaims(
        sub=user_id,
        role=role,
        actor_id=actor_id,
        full_name=full_name,
        email=email,
        department_id=department_id,
        program_id=program_id,
        iat=int(now.timestamp()),
        exp=int(expiry.timestamp()),
        jti=str(uuid.uuid4()),
    )

    return jwt.encode(claims.model_dump(), JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> JWTClaims | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return JWTClaims(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def extract_bearer_token(authorization_header: str | None) -> str | None:
    """Extract JWT token from Authorization header."""
    if not authorization_header or not authorization_header.startswith("Bearer "):
        return None
    return authorization_header.split("Bearer ", 1)[1]


# Mock user database for demonstration
MOCK_USERS = {
    "sarah.ahmed": {
        "user_id": "user_sarah_001",
        "password_hash": "mock_hash_sarah",  # In production: bcrypt.hashpw()
        "role": "student",
        "actor_id": "student_sarah_uuid",
        "full_name": "Sarah Ahmed",
        "email": "sarah.ahmed@university.edu",
        "program_id": "cs_program_uuid",
    },
    "marcus.thompson": {
        "user_id": "user_marcus_002",
        "password_hash": "mock_hash_marcus",
        "role": "student",
        "actor_id": "student_marcus_uuid",
        "full_name": "Marcus Thompson",
        "email": "marcus.thompson@university.edu",
        "program_id": "math_program_uuid",
    },
    "emily.chen": {
        "user_id": "user_emily_003",
        "password_hash": "mock_hash_emily",
        "role": "student",
        "actor_id": "student_emily_uuid",
        "full_name": "Emily Chen",
        "email": "emily.chen@university.edu",
        "program_id": "cs_program_uuid",
    },
    "dr.williams": {
        "user_id": "user_williams_004",
        "password_hash": "mock_hash_williams",
        "role": "advisor",
        "actor_id": "advisor_williams_uuid",
        "full_name": "Dr. Williams",
        "email": "williams@university.edu",
        "department_id": "cs_dept_uuid",
    },
    "dr.garcia": {
        "user_id": "user_garcia_005",
        "password_hash": "mock_hash_garcia",
        "role": "advisor",
        "actor_id": "advisor_garcia_uuid",
        "full_name": "Dr. Garcia",
        "email": "garcia@university.edu",
        "department_id": "math_dept_uuid",
    },
    "prof.johnson": {
        "user_id": "user_johnson_006",
        "password_hash": "mock_hash_johnson",
        "role": "department_head",
        "actor_id": "head_johnson_uuid",
        "full_name": "Prof. Johnson",
        "email": "johnson@university.edu",
        "department_id": "cs_dept_uuid",
    },
    "admin": {
        "user_id": "user_admin_007",
        "password_hash": "mock_hash_admin",
        "role": "registrar",
        "actor_id": "registrar_admin_uuid",
        "full_name": "System Administrator",
        "email": "admin@university.edu",
    },
}


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """Mock authentication - in production, verify against database."""
    user = MOCK_USERS.get(username)
    if not user:
        return None

    # In production: bcrypt.checkpw(password.encode('utf-8'), user['password_hash'])
    if password == "password123":  # Mock password
        return user

    return None
