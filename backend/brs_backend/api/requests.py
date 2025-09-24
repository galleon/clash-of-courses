"""Request management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from brs_backend.core.logging import log_detailed
from brs_backend.database.connection import get_db
from brs_backend.models.api import RequestCreate, RequestOut, RequestDecision
from brs_backend.models.database import Request, User

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(request: RequestCreate, db: Session = Depends(get_db)):
    """Create a new course request."""
    db_request = Request(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


@router.get("/", response_model=List[RequestOut])
def get_requests(db: Session = Depends(get_db)):
    """Get all requests."""
    requests = db.query(Request).all()
    return requests


@router.get("/{request_id}", response_model=RequestOut)
def get_request(request_id: int, db: Session = Depends(get_db)):
    """Get a specific request by ID."""
    request = db.query(Request).filter(Request.id == request_id).first()
    if request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return request
