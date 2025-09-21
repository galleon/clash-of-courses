"""FastAPI application implementing core endpoints of the BRS prototype.

This module exposes RESTful endpoints for managing users and requests. It
demonstrates how a modular backend can interact with a PostgreSQL database
via SQLAlchemy and leverage the OpenAI API to provide intelligent
assistance, such as summarising student justifications or suggesting
alternative schedules. The endpoints defined here are minimal examples
appropriate for a prototype and can be extended as needed.
"""

import os
import datetime
import logging
import json
from typing import List, Optional

import openai
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db import SessionLocal, engine
import models

# Create all tables in the database. In a production system you might use
# Alembic migrations instead of calling Base.metadata.create_all directly.
models.Base.metadata.create_all(bind=engine)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Configure OpenAI client if API key is available
openai_client = None
if OPENAI_API_KEY:
    try:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
        openai_client = None

app = FastAPI(title="BRS Prototype API", version="0.1.0")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Provide a database session for request handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    """Check system health and configuration status."""
    health_status = {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "openai_model": OPENAI_MODEL if OPENAI_API_KEY else None,
        "database": "connected",
    }

    # Test OpenAI API if configured
    if openai_client:
        try:
            openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            health_status["openai_status"] = "working"
        except Exception as e:
            health_status["openai_status"] = f"error: {str(e)[:50]}..."

    return health_status


class UserCreate(BaseModel):
    username: str
    full_name: str
    role: str
    age: Optional[int] = None
    gender: Optional[str] = None
    major: Optional[str] = None
    gpa: Optional[float] = None
    credit_hours_completed: Optional[int] = None
    technology_proficiency: Optional[str] = None
    description: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        from_attributes = True


class RequestCreate(BaseModel):
    student_id: int
    request_type: str = Field(..., pattern="^(add|drop|change)$")
    course_id: int
    section_from_id: Optional[int] = None
    section_to_id: Optional[int] = None
    justification: str


class Decision(BaseModel):
    advisor_id: int
    decision: str = Field(..., pattern="^(approve|reject|refer)$")
    department_head_id: Optional[int] = None
    rationale: Optional[str] = None


class RequestOut(BaseModel):
    id: int
    student_id: int
    request_type: str
    course_id: int
    section_from_id: Optional[int]
    section_to_id: Optional[int]
    justification: str
    status: str
    advisor_id: Optional[int]
    department_head_id: Optional[int]

    class Config:
        from_attributes = True


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class SectionOut(BaseModel):
    id: int
    course_id: int
    section_code: str
    schedule: Optional[str]
    capacity: Optional[int]
    instructor: Optional[str]
    seats_taken: Optional[int]

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
    action: Optional[str] = None
    course_info: Optional[dict] = None
    request_info: Optional[dict] = None


@app.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user account. In a prototype this might be used
    to seed additional personas or allow registration of new system
    administrators."""
    db_user = models.User(
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        age=user.age,
        gender=user.gender,
        major=user.major,
        gpa=user.gpa,
        credit_hours_completed=user.credit_hours_completed,
        technology_proficiency=user.technology_proficiency,
        description=user.description,
    )
    db.add(db_user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.refresh(db_user)
    return db_user


@app.get("/users/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    """Return a list of all users. In production you might restrict
    this to administrators or advisors."""
    users = db.query(models.User).all()
    return users


@app.post("/requests/", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(req: RequestCreate, db: Session = Depends(get_db)):
    """Submit a new add/drop/change request. A student initiates a request
    providing justification. Optionally, the system can use the OpenAI
    API to summarise the justification for advisor consumption."""
    # Summarise the justification using OpenAI if a key is available
    summary = None
    if openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant summarizing student justifications for course requests.",
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following justification in one sentence: {req.justification}",
                    },
                ],
                max_tokens=50,
            )
            summary = response.choices[0].message.content.strip()
        except Exception:
            # If the call fails (e.g., no API key), ignore and continue
            summary = None

    # Create the request record
    db_request = models.Request(
        student_id=req.student_id,
        request_type=req.request_type,
        course_id=req.course_id,
        section_from_id=req.section_from_id,
        section_to_id=req.section_to_id,
        justification=req.justification,
        status="pending",
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    # If a summary was generated, attach it to the justification as metadata
    if summary:
        db_request.justification += f"\n\n[Automated Summary]: {summary}"
        db.commit()
        db.refresh(db_request)
    return db_request


@app.get("/requests/", response_model=List[RequestOut])
def list_requests(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve all requests, optionally filtering by status. Advisors
    might use this endpoint to review pending requests."""
    query = db.query(models.Request)
    if status_filter:
        query = query.filter(models.Request.status == status_filter)
    return query.all()


@app.post("/requests/{request_id}/decision", response_model=RequestOut)
def decide_request(request_id: int, decision: Decision, db: Session = Depends(get_db)):
    """Allow an academic advisor to approve, reject, or refer a request.
    The advisor ID is recorded, and optionally a department head ID if
    the request is referred. The status is updated accordingly."""
    req = db.query(models.Request).get(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="Request is no longer pending")
    # Update advisor ID and status
    req.advisor_id = decision.advisor_id
    # Map human decisions to canonical status values
    status_map = {
        "approve": "approved",
        "reject": "rejected",
        "refer": "referred",
    }
    req.status = status_map.get(decision.decision, decision.decision)
    # If referred, assign department head
    if decision.decision == "refer":
        if not decision.department_head_id:
            raise HTTPException(
                status_code=400, detail="department_head_id required when referring"
            )
        req.department_head_id = decision.department_head_id
    # Append rationale if provided
    if decision.rationale:
        req.justification += f"\n\n[Advisor Rationale]: {decision.rationale}"
    req.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(req)
    return req


@app.get("/courses/", response_model=List[CourseOut])
def get_courses(db: Session = Depends(get_db)):
    """Get all available courses."""
    return db.query(models.Course).all()


@app.get("/courses/{course_id}/sections", response_model=List[SectionOut])
def get_course_sections(course_id: int, db: Session = Depends(get_db)):
    """Get all sections for a specific course."""
    return db.query(models.Section).filter(models.Section.course_id == course_id).all()


@app.get("/students/{student_id}/enrolled_courses")
def get_student_enrolled_courses(student_id: int, db: Session = Depends(get_db)):
    """Get courses the student is currently enrolled in based on approved requests."""
    approved_requests = (
        db.query(models.Request)
        .filter(
            models.Request.student_id == student_id,
            models.Request.status == "approved",
            models.Request.request_type == "add",
        )
        .all()
    )

    enrolled_courses = []
    for request in approved_requests:
        course = (
            db.query(models.Course)
            .filter(models.Course.id == request.course_id)
            .first()
        )
        if course:
            enrolled_courses.append(
                {
                    "id": course.id,
                    "code": course.code,
                    "name": course.name,
                    "description": course.description,
                }
            )

    return enrolled_courses


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage, db: Session = Depends(get_db)):
    """Handle student chatbot interactions for course management."""
    # Check if OpenAI is configured
    if not openai_client:
        return ChatResponse(
            response="I'm sorry, but the AI assistant is not available right now. The system administrator needs to configure the OpenAI API key. Please use the traditional form interface or contact support.",
            action="config_error",
        )

    message = chat_message.message.lower()
    student_id = chat_message.student_id

    # Get student info
    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student:
        return ChatResponse(response="Sorry, I couldn't find your student record.")

    # Get enrolled courses
    approved_requests = (
        db.query(models.Request)
        .filter(
            models.Request.student_id == student_id,
            models.Request.status == "approved",
            models.Request.request_type == "add",
        )
        .all()
    )

    enrolled_courses = []
    for request in approved_requests:
        course = (
            db.query(models.Course)
            .filter(models.Course.id == request.course_id)
            .first()
        )
        if course:
            enrolled_courses.append(course)

    # Get all available courses
    all_courses = db.query(models.Course).all()

    try:
        # Prepare detailed course information for the LLM
        enrolled_course_details = []
        for course in enrolled_courses:
            enrolled_course_details.append(
                {
                    "code": course.code,
                    "name": course.name,
                    "description": course.description or "No description available",
                }
            )

        available_course_details = []
        for course in all_courses:
            available_course_details.append(
                {
                    "code": course.code,
                    "name": course.name,
                    "description": course.description or "No description available",
                }
            )

        # Get student's request status
        all_student_requests = (
            db.query(models.Request)
            .filter(models.Request.student_id == student_id)
            .join(models.Course)
            .all()
        )

        request_status_info = []
        if all_student_requests:
            for req in all_student_requests:
                status_emoji = {
                    "pending": "🟡",
                    "approved": "✅",
                    "rejected": "❌",
                }.get(req.status, "❓")
                request_status_info.append(
                    f"- {req.course.code}: {req.request_type.upper()} request - {status_emoji} {req.status.upper()}"
                )

        # Create a more detailed system prompt with structured data
        system_prompt = f"""You are an intelligent academic advisor chatbot helping {student.full_name}, a {student.major or "student"} major.

STUDENT'S CURRENT ENROLLED COURSES:
{chr(10).join([f"- {c['code']}: {c['name']} - {c['description']}" for c in enrolled_course_details]) if enrolled_course_details else "- No courses currently enrolled"}

STUDENT'S REQUEST STATUS:
{chr(10).join(request_status_info) if request_status_info else "- No course requests submitted yet"}

ALL AVAILABLE COURSES:
{chr(10).join([f"- {c['code']}: {c['name']} - {c['description']}" for c in available_course_details])}

You can help students with:
1. **View current courses**: Show what they're enrolled in with details
2. **View request status**: Show pending, approved, or rejected course requests
3. **Check recent updates**: Show any recent changes to their course requests
4. **Browse available courses**: List and describe available courses
5. **Add course requests**: Help them request to add specific courses (requires advisor approval)
6. **Drop course requests**: Help them request to drop current courses (requires advisor approval)
7. **Course information**: Provide details about specific courses

IMPORTANT: When answering:
- Be specific and use actual course codes and names from the data above
- If asked about "available courses", list several with descriptions
- If asked about "my courses" or "enrolled courses", show their current enrollments
- For add/drop requests, be clear that these require advisor approval
- Be conversational and helpful
- When they first start chatting, ALWAYS call get_recent_updates() to check for any new status changes to their requests

Remember: You have access to the complete, up-to-date course catalog and enrollment data."""

        # Define function schemas for OpenAI function calling
        functions = [
            {
                "name": "request_add_course",
                "description": "Submit a request to add/enroll in a course. This requires advisor approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "The course code (e.g., 'CS101', 'MATH201')",
                        },
                        "justification": {
                            "type": "string",
                            "description": "Reason for wanting to add this course",
                        },
                    },
                    "required": ["course_code", "justification"],
                },
            },
            {
                "name": "request_drop_course",
                "description": "Submit a request to drop/withdraw from a course. This requires advisor approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_code": {
                            "type": "string",
                            "description": "The course code to drop (e.g., 'CS101', 'MATH201')",
                        },
                        "justification": {
                            "type": "string",
                            "description": "Reason for wanting to drop this course",
                        },
                    },
                    "required": ["course_code", "justification"],
                },
            },
            {
                "name": "get_enrolled_courses",
                "description": "Get a list of courses the student is currently enrolled in",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_available_courses",
                "description": "Get a list of all available courses with descriptions",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_request_status",
                "description": "Get the status of all course requests for this student",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_recent_updates",
                "description": "Get recent changes to course requests since the student's last login",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "since_hours": {
                            "type": "integer",
                            "description": "Number of hours back to check for updates (default: 24)",
                            "default": 24,
                        }
                    },
                    "required": [],
                },
            },
        ]

        # Use OpenAI function calling
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": chat_message.message,
                },
            ],
            functions=functions,
            function_call="auto",
            max_tokens=400,
            temperature=0.7,
        )

        message = response.choices[0].message
        ai_response = message.content or ""
        action = None
        course_info = None

        # Handle function calls
        if message.function_call:
            function_name = message.function_call.name
            function_args = json.loads(message.function_call.arguments)

            if function_name == "request_add_course":
                course_code = function_args["course_code"].replace(" ", "").upper()
                justification = function_args["justification"]

                # Find the course in our database
                course = (
                    db.query(models.Course)
                    .filter(models.Course.code == course_code)
                    .first()
                )
                if course:
                    # Check if student is already enrolled or has pending request
                    existing_request = (
                        db.query(models.Request)
                        .filter(
                            models.Request.student_id == student_id,
                            models.Request.course_id == course.id,
                            models.Request.status.in_(["pending", "approved"]),
                        )
                        .first()
                    )

                    if not existing_request:
                        # Create a new enrollment request
                        new_request = models.Request(
                            student_id=student_id,
                            course_id=course.id,
                            request_type="add",
                            justification=justification,
                            status="pending",
                            created_at=datetime.datetime.utcnow(),
                            updated_at=datetime.datetime.utcnow(),
                        )
                        db.add(new_request)
                        db.commit()

                        action = "course_requested"
                        course_info = {
                            "code": course.code,
                            "name": course.name,
                            "id": course.id,
                        }
                        ai_response += f"\n\n✅ I've submitted your enrollment request for {course.code}: {course.name}. This request will need to be approved by an advisor."
                    else:
                        ai_response += f"\n\n⚠️ You already have a {existing_request.status} request for {course.code}."
                else:
                    ai_response += f"\n\n❌ I couldn't find a course with code {course_code}. Please check the course code and try again."

            elif function_name == "request_drop_course":
                course_code = function_args["course_code"].replace(" ", "").upper()
                justification = function_args["justification"]

                course = (
                    db.query(models.Course)
                    .filter(models.Course.code == course_code)
                    .first()
                )
                if course:
                    # Check if student is enrolled
                    approved_request = (
                        db.query(models.Request)
                        .filter(
                            models.Request.student_id == student_id,
                            models.Request.course_id == course.id,
                            models.Request.status == "approved",
                            models.Request.request_type == "add",
                        )
                        .first()
                    )

                    if approved_request:
                        # Create a drop request
                        new_request = models.Request(
                            student_id=student_id,
                            course_id=course.id,
                            request_type="drop",
                            justification=justification,
                            status="pending",
                            created_at=datetime.datetime.utcnow(),
                            updated_at=datetime.datetime.utcnow(),
                        )
                        db.add(new_request)
                        db.commit()

                        action = "drop_requested"
                        course_info = {
                            "code": course.code,
                            "name": course.name,
                            "id": course.id,
                        }
                        ai_response += f"\n\n✅ I've submitted your drop request for {course.code}: {course.name}. This request will need to be approved by an advisor."
                    else:
                        ai_response += f"\n\n❌ You don't appear to be enrolled in {course_code}, so you can't drop it."
                else:
                    ai_response += f"\n\n❌ I couldn't find a course with code {course_code}. Please check the course code and try again."

            elif function_name == "get_enrolled_courses":
                if enrolled_course_details:
                    courses_list = "\n".join(
                        [
                            f"• {c['code']}: {c['name']} - {c['description']}"
                            for c in enrolled_course_details
                        ]
                    )
                    ai_response += f"\n\n📚 **Your Current Courses:**\n{courses_list}"
                else:
                    ai_response += "\n\n📚 **Your Current Courses:**\nYou are not currently enrolled in any courses."

            elif function_name == "get_available_courses":
                if available_course_details:
                    courses_list = "\n".join(
                        [
                            f"• {c['code']}: {c['name']} - {c['description']}"
                            for c in available_course_details[:10]
                        ]
                    )  # Limit to first 10
                    ai_response += f"\n\n📖 **Available Courses (showing first 10):**\n{courses_list}"
                    if len(available_course_details) > 10:
                        ai_response += f"\n\n... and {len(available_course_details) - 10} more courses available."
                else:
                    ai_response += "\n\n📖 **Available Courses:**\nNo courses are currently available."

            elif function_name == "get_request_status":
                all_student_requests = (
                    db.query(models.Request)
                    .filter(models.Request.student_id == student_id)
                    .join(models.Course)
                    .all()
                )

                if all_student_requests:
                    status_list = []
                    for req in all_student_requests:
                        status_emoji = {
                            "pending": "🟡",
                            "approved": "✅",
                            "rejected": "❌",
                        }.get(req.status, "❓")
                        status_list.append(
                            f"• {req.course.code}: {req.request_type.upper()} request - {status_emoji} {req.status.upper()}"
                        )

                    ai_response += (
                        "\n\n📋 **Your Course Request Status:**\n"
                        + "\n".join(status_list)
                    )
                else:
                    ai_response += "\n\n📋 **Your Course Request Status:**\nNo course requests submitted yet."

            elif function_name == "get_recent_updates":
                since_hours = function_args.get("since_hours", 24)
                cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(
                    hours=since_hours
                )

                # Get requests that have been updated recently
                recent_updates = (
                    db.query(models.Request)
                    .filter(models.Request.student_id == student_id)
                    .filter(models.Request.updated_at >= cutoff_time)
                    .filter(
                        models.Request.created_at != models.Request.updated_at
                    )  # Only show actually updated requests
                    .order_by(models.Request.updated_at.desc())
                    .all()
                )

                if recent_updates:
                    ai_response += "\n\n🔔 **Recent Updates to Your Requests:**\n"
                    for req in recent_updates:
                        status_emoji = {
                            "pending": "🟡",
                            "approved": "✅",
                            "rejected": "❌",
                            "referred": "🔄",
                        }.get(req.status, "❓")

                        time_diff = datetime.datetime.utcnow() - req.updated_at
                        if time_diff.days > 0:
                            time_str = f"{time_diff.days} days ago"
                        elif time_diff.seconds > 3600:
                            time_str = f"{time_diff.seconds // 3600} hours ago"
                        else:
                            time_str = f"{time_diff.seconds // 60} minutes ago"

                        ai_response += f"• **{req.course.code}** ({req.request_type.upper()}) - {status_emoji} **{req.status.upper()}** ({time_str})\n"

                        # Show advisor/department head info if available
                        if req.advisor_id:
                            advisor = (
                                db.query(models.User)
                                .filter(models.User.id == req.advisor_id)
                                .first()
                            )
                            ai_response += f"  └ Reviewed by: {advisor.full_name}\n"

                    action = "recent_updates"
                else:
                    ai_response += f"\n\n📅 **Recent Updates:**\nNo updates to your requests in the last {since_hours} hours."

        # FALLBACK: If no function was called, try keyword-based intent detection
        # This handles cases where the model doesn't support function calling properly
        if not message.function_call:
            user_message = chat_message.message.lower()

            # Pattern for course enrollment requests
            import re

            # Look for patterns like "enroll in CS201", "add CS201", "request CS201", etc.
            course_pattern = r"(?:enroll|add|request|apply|register).*?(?:for|in|to)?\s*([A-Z]{2,4}\s*\d{3,4})"
            match = re.search(course_pattern, user_message, re.IGNORECASE)

            if match:
                course_code = match.group(1).replace(" ", "").upper()

                # Find the course
                course = (
                    db.query(models.Course)
                    .filter(models.Course.code == course_code)
                    .first()
                )

                if course:
                    # Check for existing request
                    existing_request = (
                        db.query(models.Request)
                        .filter(
                            models.Request.student_id == student_id,
                            models.Request.course_id == course.id,
                            models.Request.status.in_(["pending", "approved"]),
                        )
                        .first()
                    )

                    if not existing_request:
                        # Create enrollment request
                        new_request = models.Request(
                            student_id=student_id,
                            course_id=course.id,
                            request_type="add",
                            justification=f"Student requested enrollment via chatbot: {chat_message.message}",
                            status="pending",
                            created_at=datetime.datetime.utcnow(),
                            updated_at=datetime.datetime.utcnow(),
                        )
                        db.add(new_request)
                        db.commit()

                        action = "course_requested"
                        course_info = {
                            "code": course.code,
                            "name": course.name,
                            "id": course.id,
                        }

                        ai_response += "\n\n✅ **Enrollment Request Submitted!**\n"
                        ai_response += f"I've successfully submitted your request to enroll in **{course.code}: {course.name}**.\n"
                        ai_response += "Your request is now pending advisor approval. You'll be notified once it's reviewed."
                    else:
                        ai_response += f"\n\n⚠️ You already have a **{existing_request.status}** request for {course.code}."

        return ChatResponse(
            response=ai_response, action=action, course_info=course_info
        )

    except Exception as e:
        # Log the error for debugging
        logging.error(f"OpenAI API Error in chat endpoint: {str(e)}")
        logging.error(f"API Base URL: {OPENAI_API_BASE}")
        logging.error(f"API Model: {OPENAI_MODEL}")

        # Return a proper error response instead of falling back to static responses
        return ChatResponse(
            response=f"I'm experiencing technical difficulties with the AI service right now. Please try again in a moment, or use the traditional form interface. (Error: {type(e).__name__})",
            action="ai_error",
        )


@app.post("/advisor-chat", response_model=ChatResponse)
async def advisor_chat_endpoint(
    chat_message: AdvisorChatMessage, db: Session = Depends(get_db)
):
    """Handle advisor chatbot interactions for reviewing course requests."""
    # Check if OpenAI is configured
    if not openai_client:
        return ChatResponse(
            response="I'm sorry, but the AI assistant is not available right now. The system administrator needs to configure the OpenAI API key. Please use the traditional interface or contact support.",
            action="config_error",
        )

    advisor_id = chat_message.advisor_id

    # Get advisor info
    advisor = db.query(models.User).filter(models.User.id == advisor_id).first()
    if not advisor:
        return ChatResponse(response="Sorry, I couldn't find your advisor record.")

    try:
        # Get pending requests with full details
        pending_requests = (
            db.query(models.Request).filter(models.Request.status == "pending").all()
        )

        # Build detailed request information for AI context
        request_details = []
        for req in pending_requests:
            student = (
                db.query(models.User).filter(models.User.id == req.student_id).first()
            )
            course = (
                db.query(models.Course)
                .filter(models.Course.id == req.course_id)
                .first()
            )

            request_info = {
                "id": req.id,
                "student_name": student.full_name if student else "Unknown",
                "student_major": student.major if student else "Not specified",
                "student_gpa": student.gpa if student else "Not available",
                "student_credits": student.credit_hours_completed
                if student
                else "Not available",
                "course_code": course.code if course else "Unknown",
                "course_name": course.name if course else "Unknown Course",
                "course_description": course.description
                if course
                else "No description",
                "request_type": req.request_type or "add",
                "justification": req.justification,
                "created_at": req.created_at.strftime("%Y-%m-%d %H:%M")
                if req.created_at
                else "Unknown",
            }
            request_details.append(request_info)

        # Create system prompt for advisor
        requests_summary = ""
        if request_details:
            requests_summary = "\n".join(
                [
                    f"Request #{req['id']}: {req['student_name']} wants to {req['request_type']} {req['course_code']}: {req['course_name']}"
                    for req in request_details
                ]
            )
        else:
            requests_summary = "No pending requests"

        detailed_info = ""
        if request_details:
            detailed_parts = []
            for req in request_details:
                part = f"Request #{req['id']}:\n"
                part += f"- Student: {req['student_name']} (Major: {req['student_major']}, GPA: {req['student_gpa']}, Credits: {req['student_credits']})\n"
                part += f"- Course: {req['course_code']}: {req['course_name']} - {req['course_description']}\n"
                part += f"- Type: {req['request_type']} course\n"
                part += f'- Justification: "{req["justification"]}"\n'
                part += f"- Submitted: {req['created_at']}\n"
                detailed_parts.append(part)
            detailed_info = "\n".join(detailed_parts)
        else:
            detailed_info = "No requests to review"

        system_prompt = f"""You are an intelligent academic advisor assistant helping Dr. {advisor.full_name} review course requests.

CURRENT PENDING REQUESTS ({len(request_details)} total):
{requests_summary}

DETAILED REQUEST INFORMATION:
{detailed_info}

You can help with:
1. **Reviewing requests**: Provide detailed analysis of each request with student context
2. **Making recommendations**: Suggest approve/reject/refer based on student profile and course fit
3. **Managing workflow**: Guide through requests one by one
4. **Status updates**: Check for new requests or provide summaries

IMPORTANT: When presenting requests for review:
- Provide intelligent analysis of the student's academic fit for the course
- Consider their major, GPA, and academic progress
- Explain your reasoning for recommendations
- Be conversational and helpful
- When asked to review, present ONE request at a time with full context

Be professional but conversational. You have access to complete student and course data."""

        # Define function schemas for advisor actions
        advisor_functions = [
            {
                "name": "get_pending_requests",
                "description": "Get all pending course requests that need advisor review",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "review_request",
                "description": "Review a specific course request in detail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The ID of the request to review",
                        }
                    },
                    "required": ["request_id"],
                },
            },
            {
                "name": "approve_request",
                "description": "Approve a course request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The ID of the request to approve",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Reason for approving this request",
                        },
                    },
                    "required": ["request_id", "rationale"],
                },
            },
            {
                "name": "reject_request",
                "description": "Reject a course request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The ID of the request to reject",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Reason for rejecting this request",
                        },
                    },
                    "required": ["request_id", "rationale"],
                },
            },
            {
                "name": "refer_request",
                "description": "Refer a complex request to department head",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "integer",
                            "description": "The ID of the request to refer",
                        },
                        "department_head_id": {
                            "type": "integer",
                            "description": "The ID of the department head to refer to",
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Reason for referring this request",
                        },
                    },
                    "required": ["request_id", "department_head_id", "rationale"],
                },
            },
        ]

        # Use OpenAI function calling for advisor
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": chat_message.message,
                },
            ],
            functions=advisor_functions,
            function_call="auto",
            max_tokens=600,
            temperature=0.7,
        )

        message_response = response.choices[0].message
        ai_response = message_response.content or ""
        action = None
        request_info = None

        # Handle function calls for advisor
        if message_response.function_call:
            function_name = message_response.function_call.name
            function_args = json.loads(message_response.function_call.arguments)

            if function_name == "get_pending_requests":
                if request_details:
                    requests_list = "\n".join(
                        [
                            f"• Request #{req['id']}: {req['student_name']} wants to {req['request_type']} {req['course_code']}: {req['course_name']}"
                            for req in request_details
                        ]
                    )
                    ai_response += f"\n\n📋 **Pending Requests ({len(request_details)} total):**\n{requests_list}"
                else:
                    ai_response += "\n\n📋 **Pending Requests:**\nNo pending requests at this time."

            elif function_name == "review_request":
                request_id = function_args["request_id"]
                req = next((r for r in request_details if r["id"] == request_id), None)
                if req:
                    ai_response += (
                        f"\n\n🔍 **Detailed Review - Request #{req['id']}:**\n"
                    )
                    ai_response += f"**Student:** {req['student_name']}\n"
                    ai_response += f"**Major:** {req['student_major']} | **GPA:** {req['student_gpa']} | **Credits:** {req['student_credits']}\n"
                    ai_response += (
                        f"**Course:** {req['course_code']}: {req['course_name']}\n"
                    )
                    ai_response += f"**Description:** {req['course_description']}\n"
                    ai_response += f"**Request Type:** {req['request_type'].upper()}\n"
                    ai_response += f"**Justification:** {req['justification']}\n"
                    ai_response += f"**Submitted:** {req['created_at']}\n"
                    action = "reviewing_request"
                    request_info = req
                else:
                    ai_response += f"\n\n❌ Request #{request_id} not found."

            elif function_name == "approve_request":
                request_id = function_args["request_id"]
                rationale = function_args["rationale"]

                # Find and update the request
                req = (
                    db.query(models.Request)
                    .filter(models.Request.id == request_id)
                    .first()
                )
                if req and req.status == "pending":
                    req.advisor_id = advisor_id
                    req.status = "approved"
                    req.justification += f"\n\n[Advisor Approval]: {rationale}"
                    req.updated_at = datetime.datetime.utcnow()
                    db.commit()

                    ai_response += f"\n\n✅ **Request #{request_id} APPROVED**\n"
                    ai_response += f"Student {req.student.full_name} can now {req.request_type} {req.course.code}."
                    action = "approve_request"
                else:
                    ai_response += (
                        f"\n\n❌ Request #{request_id} not found or already processed."
                    )

            elif function_name == "reject_request":
                request_id = function_args["request_id"]
                rationale = function_args["rationale"]

                req = (
                    db.query(models.Request)
                    .filter(models.Request.id == request_id)
                    .first()
                )
                if req and req.status == "pending":
                    req.advisor_id = advisor_id
                    req.status = "rejected"
                    req.justification += f"\n\n[Advisor Rejection]: {rationale}"
                    req.updated_at = datetime.datetime.utcnow()
                    db.commit()

                    ai_response += f"\n\n❌ **Request #{request_id} REJECTED**\n"
                    ai_response += f"Student {req.student.full_name} has been notified."
                    action = "reject_request"
                else:
                    ai_response += (
                        f"\n\n❌ Request #{request_id} not found or already processed."
                    )

            elif function_name == "refer_request":
                request_id = function_args["request_id"]
                department_head_id = function_args["department_head_id"]
                rationale = function_args["rationale"]

                req = (
                    db.query(models.Request)
                    .filter(models.Request.id == request_id)
                    .first()
                )
                if req and req.status == "pending":
                    req.advisor_id = advisor_id
                    req.department_head_id = department_head_id
                    req.status = "referred"
                    req.justification += f"\n\n[Advisor Referral]: {rationale}"
                    req.updated_at = datetime.datetime.utcnow()
                    db.commit()

                    ai_response += f"\n\n🔄 **Request #{request_id} REFERRED**\n"
                    ai_response += (
                        "Request has been escalated to department head for review."
                    )
                    action = "refer_request"
                else:
                    ai_response += (
                        f"\n\n❌ Request #{request_id} not found or already processed."
                    )

        return ChatResponse(
            response=ai_response, action=action, request_info=request_info
        )

    except Exception as e:
        # Log the error for debugging
        logging.error(f"OpenAI API Error in advisor chat endpoint: {str(e)}")
        logging.error(f"API Base URL: {OPENAI_API_BASE}")
        logging.error(f"API Model: {OPENAI_MODEL}")

        # Return a proper error response
        return ChatResponse(
            response=f"I'm experiencing technical difficulties with the AI service right now. Please try again in a moment, or use the traditional interface. (Error: {type(e).__name__})",
            action="ai_error",
        )
