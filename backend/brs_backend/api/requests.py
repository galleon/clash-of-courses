"""Request management API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from brs_backend.core.logging import log_detailed
from brs_backend.database.connection import get_db
from uuid import UUID

from brs_backend.models.api import (
    RegistrationRequestCreate,
    RegistrationRequestOut,
    RequestDecision,
)
from brs_backend.models.database import RegistrationRequest, User

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "/", response_model=RegistrationRequestOut, status_code=status.HTTP_201_CREATED
)
def create_request(request: RegistrationRequestCreate, db: Session = Depends(get_db)):
    """Create a new course request."""
    db_request = RegistrationRequest(**request.model_dump())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@router.get("/", response_model=list[RegistrationRequestOut])
def list_requests(db: Session = Depends(get_db)):
    """List all requests."""
    return db.query(RegistrationRequest).all()


@router.get("/{request_id}", response_model=RegistrationRequestOut)
def get_request(request_id: UUID, db: Session = Depends(get_db)):
    """Get a specific request by ID."""
    request = (
        db.query(RegistrationRequest)
        .filter(RegistrationRequest.request_id == request_id)
        .first()
    )
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request
