"""User authentication and mapping service."""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from brs_backend.models.database import User, Student, Instructor
from brs_backend.database.connection import get_db


class UserService:
    """Service for mapping authenticated users to database entities."""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        """Get user by username from database."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_entity_info(db: Session, user: User) -> dict[str, Any]:
        """Get the linked entity info (Student/Instructor) for a user."""
        if user.role == "student" and user.student_id:
            student = (
                db.query(Student).filter(Student.student_id == user.student_id).first()
            )
            if student:
                return {
                    "entity_id": str(student.student_id),
                    "entity_type": "student",
                    "external_id": student.external_sis_id,
                    "entity": student,
                }
        elif user.role in ["advisor", "instructor"] and user.instructor_id:
            instructor = (
                db.query(Instructor)
                .filter(Instructor.instructor_id == user.instructor_id)
                .first()
            )
            if instructor:
                return {
                    "entity_id": str(instructor.instructor_id),
                    "entity_type": "instructor",
                    "external_id": None,
                    "entity": instructor,
                }

        # Fallback for users without linked entities
        return {
            "entity_id": f"{user.role}_{user.username}",
            "entity_type": user.role,
            "external_id": user.username,
            "entity": None,
        }

    @staticmethod
    def create_demo_users_and_links(db: Session):
        """Create demo users and link them to existing Student/Instructor records."""

        # Get existing students by external_sis_id
        sarah_student = (
            db.query(Student).filter(Student.external_sis_id == "S1001").first()
        )
        marcus_student = (
            db.query(Student).filter(Student.external_sis_id == "S1002").first()
        )
        emily_student = (
            db.query(Student).filter(Student.external_sis_id == "S1003").first()
        )

        # Get instructors (just get first two since we can't query by name reliably)
        instructors = db.query(Instructor).limit(2).all()
        ahmad_instructor = instructors[0] if len(instructors) > 0 else None
        layla_instructor = instructors[1] if len(instructors) > 1 else None

        demo_users = [
            {
                "username": "sarah.ahmed",
                "full_name": "Sarah Ahmed",
                "user_type": "student",
                "email": "sarah.ahmed@university.edu",
                "student_id": sarah_student.student_id if sarah_student else None,
            },
            {
                "username": "marcus.thompson",
                "full_name": "Marcus Thompson",
                "user_type": "student",
                "email": "marcus.thompson@university.edu",
                "student_id": marcus_student.student_id if marcus_student else None,
            },
            {
                "username": "emily.chen",
                "full_name": "Emily Chen",
                "user_type": "student",
                "email": "emily.chen@university.edu",
                "student_id": emily_student.student_id if emily_student else None,
            },
            {
                "username": "dr.rodriguez",
                "full_name": "Dr. Maria Rodriguez",
                "user_type": "instructor",
                "email": "maria.rodriguez@university.edu",
                "instructor_id": ahmad_instructor.instructor_id
                if ahmad_instructor
                else None,
            },
            {
                "username": "prof.kim",
                "full_name": "Prof. David Kim",
                "user_type": "instructor",
                "email": "david.kim@university.edu",
                "instructor_id": layla_instructor.instructor_id
                if layla_instructor
                else None,
            },
            {
                "username": "dr.johnson",
                "full_name": "Dr. Jennifer Johnson",
                "user_type": "department_head",
                "email": "jennifer.johnson@university.edu",
            },
            {
                "username": "admin.user",
                "full_name": "System Admin",
                "user_type": "system_admin",
                "email": "admin@university.edu",
            },
        ]

        for user_data in demo_users:
            existing_user = (
                db.query(User).filter(User.username == user_data["username"]).first()
            )
            if not existing_user:
                user = User(**user_data)
                db.add(user)

        db.commit()
