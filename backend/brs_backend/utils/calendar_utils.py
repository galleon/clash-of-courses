"""Calendar utilities for standard calendar format conversion."""

import uuid
from datetime import datetime, timedelta
from typing import Any

from icalendar import Calendar, Event

from brs_backend.models.tool_outputs import CalendarEvent, ScheduleItem, StudentSchedule


def create_ical_event(schedule_item: ScheduleItem, term_start: datetime) -> Event:
    """Convert a schedule item to an iCal Event.

    Args:
        schedule_item: Student schedule item (course meeting)
        term_start: Start date of the academic term

    Returns:
        iCal Event object
    """
    event = Event()

    # Generate unique ID
    event.add(
        "uid",
        f"{schedule_item.course_code}-{schedule_item.section_code}-{uuid.uuid4()}",
    )
    event.add("summary", f"{schedule_item.course_code} - {schedule_item.course_title}")
    event.add(
        "description",
        f"Section {schedule_item.section_code} with {schedule_item.instructor}",
    )

    # Process each meeting time
    for meeting in schedule_item.meetings:
        # Calculate the date of first occurrence based on day_of_week
        days_until_meeting = meeting.day_of_week - term_start.weekday()
        if days_until_meeting < 0:
            days_until_meeting += 7

        first_occurrence = term_start + timedelta(days=days_until_meeting)

        # Parse time
        start_time_parts = meeting.start_time.split(":")
        end_time_parts = meeting.end_time.split(":")

        dtstart = first_occurrence.replace(
            hour=int(start_time_parts[0]),
            minute=int(start_time_parts[1]),
            second=int(start_time_parts[2]) if len(start_time_parts) > 2 else 0,
        )

        dtend = first_occurrence.replace(
            hour=int(end_time_parts[0]),
            minute=int(end_time_parts[1]),
            second=int(end_time_parts[2]) if len(end_time_parts) > 2 else 0,
        )

        event.add("dtstart", dtstart)
        event.add("dtend", dtend)

        # Add recurrence rule for weekly meetings
        event.add("rrule", {"freq": "weekly", "count": 15})  # 15 weeks typical semester

        if meeting.room:
            event.add("location", meeting.room)

        event.add("categories", [schedule_item.course_code, meeting.activity])

        # Set status based on enrollment status
        if schedule_item.status == "enrolled":
            event.add("status", "CONFIRMED")
        else:
            event.add("status", "TENTATIVE")

    return event


def schedule_to_ical(schedule: StudentSchedule, term_start: datetime) -> str:
    """Convert a student schedule to iCal format string.

    Args:
        schedule: Complete student schedule
        term_start: Start date of the academic term

    Returns:
        iCal format string
    """
    cal = Calendar()
    cal.add("prodid", "-//BRS Student Registration System//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")

    # Add metadata
    cal.add("x-wr-calname", f"Student Schedule - {schedule.total_credits} credits")
    cal.add(
        "x-wr-caldesc",
        f"Academic schedule with {schedule.course_count} enrolled courses",
    )

    # Convert each schedule item to events
    for item in schedule.schedule:
        event = create_ical_event(item, term_start)
        cal.add_component(event)

    return cal.to_ical().decode("utf-8")


def create_calendar_event(
    summary: str,
    start_time: datetime,
    end_time: datetime,
    description: str = None,
    location: str = None,
    recurrence: str = None,
) -> CalendarEvent:
    """Create a standard CalendarEvent from basic parameters.

    Args:
        summary: Event title
        start_time: Event start datetime
        end_time: Event end datetime
        description: Optional event description
        location: Optional event location
        recurrence: Optional recurrence rule string

    Returns:
        CalendarEvent object
    """
    return CalendarEvent(
        uid=str(uuid.uuid4()),
        summary=summary,
        description=description,
        dtstart=start_time,
        dtend=end_time,
        location=location,
        status="confirmed",
    )


def parse_meeting_time(time_str: str) -> tuple[int, int, int]:
    """Parse time string to hour, minute, second tuple.

    Args:
        time_str: Time in HH:MM:SS or HH:MM format

    Returns:
        Tuple of (hour, minute, second)
    """
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0
    return hour, minute, second


def get_term_dates(term_id: str = None) -> tuple[datetime, datetime]:
    """Get term start and end dates.

    Args:
        term_id: Optional term identifier

    Returns:
        Tuple of (term_start, term_end) datetimes
    """
    # Default to current academic year dates
    # In production, this would query the database for term dates
    current_year = datetime.now().year

    # Spring semester (January - May)
    if datetime.now().month <= 5:
        term_start = datetime(current_year, 1, 15)
        term_end = datetime(current_year, 5, 15)
    # Fall semester (August - December)
    else:
        term_start = datetime(current_year, 8, 20)
        term_end = datetime(current_year, 12, 15)

    return term_start, term_end


def create_course_calendar_events(
    course_code: str,
    section_code: str,
    meetings: list[dict[str, Any]],
    instructor: str,
    term_start: datetime = None,
) -> list[CalendarEvent]:
    """Create calendar events for a course's meetings.

    Args:
        course_code: Course code (e.g., "CS101")
        section_code: Section code (e.g., "A1")
        meetings: List of meeting dictionaries
        instructor: Instructor name
        term_start: Term start date (defaults to current term)

    Returns:
        List of CalendarEvent objects
    """
    if term_start is None:
        term_start, _ = get_term_dates()

    events = []

    for meeting in meetings:
        # Calculate first occurrence date
        days_until_meeting = meeting["day_of_week"] - term_start.weekday()
        if days_until_meeting < 0:
            days_until_meeting += 7

        first_occurrence = term_start + timedelta(days=days_until_meeting)

        # Parse times
        start_hour, start_min, start_sec = parse_meeting_time(meeting["start_time"])
        end_hour, end_min, end_sec = parse_meeting_time(meeting["end_time"])

        dtstart = first_occurrence.replace(
            hour=start_hour, minute=start_min, second=start_sec
        )
        dtend = first_occurrence.replace(hour=end_hour, minute=end_min, second=end_sec)

        event = CalendarEvent(
            uid=f"{course_code}-{section_code}-{meeting['day_name']}-{uuid.uuid4()}",
            summary=f"{course_code} {meeting['activity']}",
            description=f"Section {section_code} with {instructor}",
            dtstart=dtstart,
            dtend=dtend,
            location=meeting.get("room"),
            categories=[course_code, meeting["activity"]],
            status="confirmed",
        )

        events.append(event)

    return events
