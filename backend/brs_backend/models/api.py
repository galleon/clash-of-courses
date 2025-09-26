"""Pydantic models for API request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    age: int | None = None
    gender: str | None = None
    major: str | None = None
    gpa: float | None = None
    credit_hours_completed: int | None = None


class UserCreate(UserBase):
    pass


class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CourseBase(BaseModel):
    code: str
    title: str
    description: str | None = None
    credits: int | None = 3
    level: int | None = 100
    prerequisites: str | None = None


class CourseOut(CourseBase):
    course_id: UUID  # UUID will be automatically serialized to string

    model_config = ConfigDict(from_attributes=True)


class RegistrationRequestBase(BaseModel):
    student_id: UUID  # UUID as string
    to_section_id: UUID | None = None  # UUID as string
    from_section_id: UUID | None = None  # UUID as string
    type: str = "ADD"  # ADD, DROP, CHANGE_SECTION
    justification: str | None = None


class RegistrationRequestCreate(RegistrationRequestBase):
    pass


class RegistrationRequestOut(RegistrationRequestBase):
    request_id: UUID  # UUID as string
    state: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatMessage(BaseModel):
    message: str
    student_id: int


class AdvisorChatMessage(BaseModel):
    message: str
    advisor_id: int


class ChatResponse(BaseModel):
    response: str
    action: str | None = None
    course_info: dict | None = None


class RequestDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    rationale: str
