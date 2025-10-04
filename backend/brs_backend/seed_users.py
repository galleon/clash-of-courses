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
from brs_backend.models.database import User, Student, Instructor


def _uuid():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def seed_users():
    """Create User authentication records for students, instructors, and admin."""

    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        # Get actual students from database
        students = session.query(Student).all()

        # Get actual instructors from database
        instructors = session.query(Instructor).all()

        users_to_create = []

        # Create users for all students
        student_usernames = [
            "sarah.ahmed", "mohammed.hassan", "fatima.alzahra", "alex.johnson", "maria.garcia",
            "david.smith", "lisa.chen", "michael.brown", "jennifer.davis", "robert.wilson",
            "anna.miller", "james.moore", "jessica.taylor", "christopher.anderson", "amanda.thomas",
            "matthew.jackson", "ashley.white", "joshua.harris", "stephanie.martin", "andrew.thompson",
            "michelle.garcia", "daniel.martinez", "kimberly.robinson", "ryan.clark", "laura.rodriguez",
            "kevin.lewis", "nicole.lee", "brandon.walker", "elizabeth.hall", "tyler.allen",
            "rachel.young", "jacob.hernandez", "samantha.king", "nathaniel.wright", "megan.lopez",
            "jonathan.hill", "lauren.scott", "nicholas.green", "brittany.adams", "austin.baker",
            "kayla.gonzalez", "cameron.nelson", "danielle.carter"
        ]

        for i, student in enumerate(students):
            username = student_usernames[i] if i < len(student_usernames) else f"student{i+1}"
            # Extract first and last name from username for email and full name
            name_parts = username.replace(".", " ").title()

            users_to_create.append({
                "username": username,
                "email": f"{username}@university.edu",
                "full_name": name_parts,
                "user_type": "student",
                "password": "password123",
                "student_id": str(student.student_id)
            })

        # Create users for all instructors
        instructor_data = [
            {"name": "Dr. Ahmad Mahmoud", "username": "ahmad.mahmoud"},
            {"name": "Dr. Layla Khalil", "username": "layla.khalil"},
            {"name": "Dr. Omar Al-Rashid", "username": "omar.alrashid"},
            {"name": "Prof. Sara Qasemi", "username": "sara.qasemi"},
            {"name": "Dr. Hassan Nouri", "username": "hassan.nouri"},
            {"name": "Dr. Fatma Al-Zaidi", "username": "fatma.alzaidi"},
            {"name": "Prof. Kareem Mansouri", "username": "kareem.mansouri"}
        ]

        for i, instructor in enumerate(instructors):
            if i < len(instructor_data):
                instructor_info = instructor_data[i]
                username = instructor_info["username"]
                full_name = instructor_info["name"]
            else:
                username = f"instructor{i+1}"
                full_name = f"Instructor {i+1}"

            users_to_create.append({
                "username": username,
                "email": f"{username}@university.edu",
                "full_name": full_name,
                "user_type": "instructor",
                "password": "instructor123",
                "instructor_id": str(instructor.instructor_id)
            })

        # Add system admin
        users_to_create.append({
            "username": "admin",
            "email": "admin@university.edu",
            "full_name": "System Administrator",
            "user_type": "system_admin",
            "password": "admin123",
            "admin_id": _uuid()
        })

        # Create each user
        for user_data in users_to_create:
            username = user_data["username"]

            # Check if user already exists
            existing_user = session.query(User).filter(User.username == username).first()
            if existing_user:
                print(f"User {username} already exists, skipping...")
                continue

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
        print(f"\nUser seeding completed successfully! Created {len(users_to_create)} users.")
        print(f"  Students: {len([u for u in users_to_create if u['user_type'] == 'student'])}")
        print(f"  Instructors: {len([u for u in users_to_create if u['user_type'] == 'instructor'])}")
        print(f"  Admins: {len([u for u in users_to_create if u['user_type'] == 'system_admin'])}")

        print("\nKey login credentials:")
        print("  sarah.ahmed / password123 (student)")
        print("  ahmad.mahmoud / instructor123 (instructor)")
        print("  admin / admin123 (system admin)")


if __name__ == "__main__":
    seed_users()
