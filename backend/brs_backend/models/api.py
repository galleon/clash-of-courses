"""Pydantic models for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True


class CourseBase(BaseModel):
    code: str
    name: str
    title: str | None = None
    description: str | None = None
    credits: int | None = 3
    prerequisites: str | None = None


class CourseOut(CourseBase):
    id: int

    class Config:
        from_attributes = True


class RequestBase(BaseModel):
    student_id: int
    course_id: int
    request_type: str = "add"
    justification: str


class RequestCreate(RequestBase):
    pass


class RequestOut(RequestBase):
    id: int
    status: str
    advisor_id: int | None = None
    department_head_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


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
