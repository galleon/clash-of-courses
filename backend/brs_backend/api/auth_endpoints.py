"""Authentication endpoints for BRS JWT-based login system."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brs_backend.auth.jwt_handler import authenticate_user, create_jwt_token


router = APIRouter(prefix="/v1/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request with username and password."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token and user info."""

    token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    full_name: str
    expires_in: int = 86400  # 24 hours in seconds


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create JWT token
    token = create_jwt_token(
        user_id=user["user_id"],
        role=user["role"],
        actor_id=user["actor_id"],
        full_name=user["full_name"],
        email=user.get("email"),
        department_id=user.get("department_id"),
        program_id=user.get("program_id"),
    )

    return LoginResponse(
        token=token,
        user_id=user["user_id"],
        role=user["role"],
        full_name=user["full_name"],
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (token revocation would be implemented here)."""
    # In a production system, you would:
    # 1. Add the JWT to a blacklist/revocation list
    # 2. Store revoked tokens in Redis/database with expiry
    # 3. Check blacklist in the JWT validation middleware

    return {"message": "Logged out successfully"}


class TokenValidationResponse(BaseModel):
    """Token validation response."""

    valid: bool
    user_id: str
    role: str
    full_name: str
    expires_at: int


@router.get("/validate", response_model=TokenValidationResponse)
async def validate_token(authorization: str = None):
    """Validate JWT token and return user info."""
    from brs_backend.auth.jwt_handler import extract_bearer_token, decode_jwt_token

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    claims = decode_jwt_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return TokenValidationResponse(
        valid=True,
        user_id=claims.sub,
        role=claims.role,
        full_name=claims.full_name,
        expires_at=claims.exp,
    )
