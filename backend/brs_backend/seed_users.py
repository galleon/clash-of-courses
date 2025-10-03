"""
Seed script for User authentication records.

This script creates User table entries that correspond to the personas
created in seed_personas.py. It establishes the authentication layer
that allows students, instructors, and administrators to log into the system.

The User table uses a composition pattern where each user record links
to exactly one domain entity (student, instructor, department_head, or admin).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from brs_backend.database.connection import engine, Base
from brs_backend.models.database import User, Student


def seed_users():
    """Create User authentication records for the personas from seed_personas.py."""
    
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    with Session(engine) as session:
        # Define all users to create
        users_to_create = [
            # Students
            {
                "username": "sarah.ahmed",
                "email": "sarah.ahmed@university.edu",
                "full_name": "Sarah Ahmed",
                "user_type": "student",
                "password": "password123",
                "student_id": "4441ab90-e2fe-4da5-a0e1-6a129d61552f"  # Fixed UUID from seed_personas
            },
            {
                "username": "marcus.thompson", 
                "email": "marcus.thompson@university.edu",
                "full_name": "Marcus Thompson",
                "user_type": "student",
                "password": "password123",
                "student_id": str(uuid.uuid4())
            },
            {
                "username": "emily.chen",
                "email": "emily.chen@university.edu", 
                "full_name": "Emily Chen",
                "user_type": "student",
                "password": "password123",
                "student_id": str(uuid.uuid4())
            },
            # Academic Advisors
            {
                "username": "dr.rodriguez",
                "email": "dr.rodriguez@university.edu",
                "full_name": "Dr. Rodriguez", 
                "user_type": "advisor",
                "password": "advisor123",
                "instructor_id": str(uuid.uuid4())
            },
            {
                "username": "prof.kim",
                "email": "prof.kim@university.edu",
                "full_name": "Prof. Kim",
                "user_type": "advisor", 
                "password": "advisor123",
                "instructor_id": str(uuid.uuid4())
            },
            # Department Head
            {
                "username": "dr.johnson",
                "email": "dr.johnson@university.edu",
                "full_name": "Dr. Johnson",
                "user_type": "department_head",
                "password": "head123", 
                "department_head_id": str(uuid.uuid4())
            },
            # System Admin
            {
                "username": "admin.user",
                "email": "admin.user@university.edu",
                "full_name": "Admin User",
                "user_type": "system_admin",
                "password": "admin123",
                "admin_id": str(uuid.uuid4())
            }
        ]
        
        # Create each user
        for user_data in users_to_create:
            username = user_data["username"]
            
            # Since we're dropping tables, no need to check for existing users
            user = User(
                username=username,
                email=user_data["email"],
                full_name=user_data["full_name"], 
                user_type=user_data["user_type"],
                password_hash=user_data["password"],  # In production, this should be hashed
                is_active=1
            )
            
            # Set the appropriate entity reference
            if "student_id" in user_data:
                user.student_id = user_data["student_id"] 
            elif "instructor_id" in user_data:
                user.instructor_id = user_data["instructor_id"]
            elif "department_head_id" in user_data:
                user.department_head_id = user_data["department_head_id"]
            elif "admin_id" in user_data:
                user.admin_id = user_data["admin_id"]
            
            session.add(user)
            print(f"Created user: {username} ({user_data['user_type']}) - password: {user_data['password']}")
        
        session.commit()
        print("User seeding completed successfully!")
        print("\nLogin credentials:")
        for user_data in users_to_create:
            print(f"  {user_data['username']} / {user_data['password']} ({user_data['user_type']})")


if __name__ == "__main__":
    seed_users()