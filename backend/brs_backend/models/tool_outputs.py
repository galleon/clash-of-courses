"""Pydantic models for structured tool outputs - LangGraph migration."""

from datetime import datetime, time, date
from typing import Any, Union, Literal

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict
from uuid import UUID

from pydantic import BaseModel, Field, validator


# Base response models
class BaseToolResponse(BaseModel):
    """Base response class for all agent tool outputs."""

    success: bool = True
    message: str = ""
    error: str | None = None
    preferred_card_types: list[str] = Field(default_factory=lambda: ["generic"])


# Calendar and Time Models
class CalendarEvent(BaseModel):
    """Standard calendar event following iCal format."""

    uid: str = Field(description="Unique identifier for the event")
    summary: str = Field(description="Event title/summary")
    description: str | None = None
    dtstart: datetime = Field(description="Event start time")
    dtend: datetime = Field(description="Event end time")
    location: str | None = None
    organizer: str | None = None
    attendees: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    status: Literal["confirmed", "tentative", "cancelled"] = "confirmed"

    @validator("dtend")
    def end_after_start(cls, v, values):
        if "dtstart" in values and v <= values["dtstart"]:
            raise ValueError("End time must be after start time")
        return v


class RecurrenceRule(BaseModel):
    """iCal recurrence rule (RRULE)."""

    freq: Literal["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
    interval: int = 1
    count: int | None = None
    until: date | None = None
    byday: list[str] | None = None  # MO, TU, WE, TH, FR, SA, SU
    bymonthday: list[int] | None = None
    bymonth: list[int] | None = None


class CalendarEventComplete(CalendarEvent):
    """Complete calendar event with recurrence and exceptions."""

    rrule: RecurrenceRule | None = None
    exdate: list[datetime] = Field(default_factory=list, description="Exception dates")


# Meeting and Section Models
class SectionMeeting(BaseModel):
    """Meeting time information for a course section."""

    day: str = Field(description="Day of week (Monday, Tuesday, etc.)")
    start_time: str = Field(description="Start time (HH:MM format)")
    end_time: str = Field(description="End time (HH:MM format)")
    room: str | None = None


class SectionInfo(BaseModel):
    """Section information with meetings."""

    section_id: str
    section_code: str
    instructor: str
    capacity: int
    enrolled: int
    available: int
    meetings: list[SectionMeeting]


class CourseInfo(BaseModel):
    """Course information with sections."""

    course_id: str
    code: str
    title: str
    credits: int
    sections: list[SectionInfo]


# Student and Schedule Models
class ScheduleItem(BaseModel):
    """Individual schedule item (enrollment or pending request)."""

    course_code: str
    course_title: str
    credits: int
    section_code: str
    instructor: str
    meetings: list[SectionMeeting]
    status: Literal["enrolled", "pending"]

    # Optional fields based on status
    enrollment_id: str | None = None
    enrolled_at: str | None = None
    request_id: str | None = None
    requested_at: str | None = None


class StudentSchedule(BaseModel):
    """Complete student schedule."""

    student_id: str
    term_id: str | None = None
    total_credits: int
    pending_credits: int
    course_count: int
    pending_count: int
    schedule: list[ScheduleItem]


# Conflict and Violation Models
class Violation(BaseModel):
    """Business rule violation."""

    rule_code: str
    message: str
    severity: Literal["error", "warning"]


class ConflictItem(BaseModel):
    """Schedule conflict item."""

    type: str = Field(
        description="Type of conflict (time_conflict, prerequisite, etc.)"
    )
    description: str = Field(description="Human-readable conflict description")
    course_code: str = Field(description="Course code involved in conflict")
    day: str | None = None
    time_range: str | None = None
    conflicting_course: str | None = None
    severity: Literal["low", "medium", "high"] = "medium"


class AlternativeSection(BaseModel):
    """Alternative section suggestion."""

    section_id: str
    section_code: str
    instructor: str
    capacity: int
    enrolled: int
    available: int
    meetings: list[SectionMeeting]
    reason: str


# Tool Response Models
class ScheduleResponse(BaseToolResponse):
    """Response for get_current_schedule."""

    data: StudentSchedule | None = None


class CourseSearchResponse(BaseToolResponse):
    """Response for course/section search operations."""

    data: dict | None = None  # Will contain courses list and metadata


class AttachabilityResponse(BaseToolResponse):
    """Response for check_attachable."""

    attachable: bool = False
    reason: str = Field(description="Reason why attachable/not attachable")
    section_info: dict[str, Any] = Field(
        default_factory=dict, description="Section details"
    )
    conflicts: list[ConflictItem] = Field(
        default_factory=list, description="Schedule conflicts"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Action recommendations"
    )
    violations: list[Violation] = Field(
        default_factory=list, description="Business rule violations"
    )
    suggested_alternatives: list[AlternativeSection] = Field(
        default_factory=list, description="Alternative sections"
    )
    data: dict | None = None


class EnrollmentResponse(BaseToolResponse):
    """Response for enrollment operations."""

    success: bool = False
    message: str = Field(description="Human-readable result message")
    enrollment_id: str | None = None
    updated_schedule: StudentSchedule | None = None
    conflicts: list[ConflictItem] = Field(default_factory=list)
    transaction_id: str = Field(description="Unique transaction identifier")

    # Legacy fields for backward compatibility
    section_code: str | None = None
    course_code: str | None = None
    course_title: str | None = None
    enrolled_at: str | None = None
    auto_enrolled: bool = False

    # For conflict resolution
    conflict_detected: bool = False
    requested_section: str | None = None
    alternative_used: str | None = None
    conflict_reason: str | None = None
    resolution_message: str | None = None

    # Include updated schedule data (alias for updated_schedule)
    schedule_data: StudentSchedule | None = None


class RegistrationRequestResponse(BaseToolResponse):
    """Response for registration request creation."""

    data: dict | None = None


class StudentInfoResponse(BaseToolResponse):
    """Response for student information."""

    data: dict | None = None


# Calendar Integration Models
class CalendarSyncRequest(BaseModel):
    """Request to sync schedule with external calendar."""

    student_id: str
    calendar_format: Literal["ical", "google", "outlook"] = "ical"
    term_id: str | None = None
    include_pending: bool = False


class CalendarSyncResponse(BaseToolResponse):
    """Response for calendar sync operations."""

    calendar_data: str | None = None  # iCal format string
    events_count: int = 0
    format: str = "ical"
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)


# LangGraph State Models
class BRSAgentState(TypedDict):
    """State model for BRS LangGraph agent."""

    messages: list[Any]  # LangChain messages (HumanMessage, AIMessage, etc.)
    student_id: str | None
    last_action: str | None
    metadata: dict[str, Any]


# Schedule Analysis Models
class ScheduleConflict(BaseModel):
    """Detected schedule conflict."""

    conflict_type: Literal["time", "prerequisite", "capacity", "academic_standing"]
    severity: Literal["error", "warning"]
    description: str
    affected_courses: list[str]
    suggested_resolution: str | None = None


class ScheduleAnalysis(BaseModel):
    """Complete schedule analysis."""

    total_credits: int
    conflicts: list[ScheduleConflict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    optimization_score: float = Field(
        ge=0.0, le=1.0, description="Schedule quality score"
    )

    @validator("optimization_score")
    def score_valid(cls, v):
        return round(v, 2)


class ScheduleAnalysisResponse(BaseToolResponse):
    """Response for schedule analysis."""

    analysis: ScheduleAnalysis | None = None
