"""Seed the database with personas defined in the BRS document.

Run this script after database tables have been created (e.g. via
models.Base.metadata.create_all) to populate the users table with
representative personas. The personas correspond to the examples
described in the Business Requirements Specification: three students,
two academic advisors, one department head, and one system administrator.
"""

import argparse
from sqlalchemy.orm import Session

from brs_backend.database.connection import SessionLocal, engine
from brs_backend.models.database import User, Base, Course, Section, Request


def main(enroll_sarah=False):
    import sys

    print("🚀 Starting seed_personas.py script", flush=True)

    # Create all tables first
    Base.metadata.create_all(bind=engine)
    print("📋 Database tables created/verified", flush=True)

    # Always clear all data first for a fresh start
    print("🔄 Resetting database - clearing all data...", flush=True)
    db = SessionLocal()
    try:
        # Clear all tables in reverse dependency order
        requests_deleted = db.query(Request).delete()
        sections_deleted = db.query(Section).delete()
        courses_deleted = db.query(Course).delete()
        users_deleted = db.query(User).delete()
        db.commit()
        print("✅ Database cleared successfully:", flush=True)
        print(f"   - Requests deleted: {requests_deleted}", flush=True)
        print(f"   - Sections deleted: {sections_deleted}", flush=True)
        print(f"   - Courses deleted: {courses_deleted}", flush=True)
        print(f"   - Users deleted: {users_deleted}", flush=True)
    except Exception as e:
        print(f"❌ Error clearing database: {e}", flush=True)
        db.rollback()
        return
    finally:
        db.close()

    personas = [
        {
            "username": "sarah.ahmed",
            "full_name": "Sarah Ahmed",
            "role": "student",
            "age": 19,
            "gender": "Female",
            "major": "Computer Engineering",
            "gpa": 3.2,
            "credit_hours_completed": 45,
            "technology_proficiency": "High",
            "description": "Proactive planner with an interest in optimizing her schedule.",
        },
        {
            "username": "mohammed.hassan",
            "full_name": "Mohammed Hassan",
            "role": "student",
            "age": 22,
            "gender": "Male",
            "major": "Business Administration",
            "gpa": 2.8,
            "credit_hours_completed": 110,
            "technology_proficiency": "Medium",
            "description": "Balances work and study, looking to meet graduation requirements efficiently.",
        },
        {
            "username": "fatima.zahra",
            "full_name": "Fatima Al-Zahra",
            "role": "student",
            "age": 18,
            "gender": "Female",
            "major": "Pre-Medical Track",
            "gpa": 3.8,
            "credit_hours_completed": 15,
            "technology_proficiency": "High",
            "description": "Rule-follower and digital native with limited flexibility in course selection.",
        },
        {
            "username": "dr.ahmad",
            "full_name": "Dr. Ahmad Mahmoud",
            "role": "advisor",
            "age": 45,
            "gender": "Male",
            "major": "Mechanical Engineering",
            "gpa": None,
            "credit_hours_completed": None,
            "technology_proficiency": "Medium",
            "description": "Engineering academic advisor with data-driven decision making.",
        },
        {
            "username": "dr.layla",
            "full_name": "Dr. Layla Khalil",
            "role": "advisor",
            "age": 38,
            "gender": "Female",
            "major": "Business Administration",
            "gpa": None,
            "credit_hours_completed": None,
            "technology_proficiency": "High",
            "description": "Business college advisor who embraces technology for personalized guidance.",
        },
        {
            "username": "prof.hassan",
            "full_name": "Prof. Hassan Al-Rashid",
            "role": "department_head",
            "age": 52,
            "gender": "Male",
            "major": "Electrical Engineering",
            "gpa": None,
            "credit_hours_completed": None,
            "technology_proficiency": "Medium",
            "description": "Engineering department head focused on policy and strategic oversight.",
        },
        {
            "username": "omar.farid",
            "full_name": "Omar Farid",
            "role": "system_admin",
            "age": 32,
            "gender": "Male",
            "major": "Information Technology",
            "gpa": None,
            "credit_hours_completed": None,
            "technology_proficiency": "Expert",
            "description": "IT systems administrator responsible for maintenance and user support.",
        },
    ]

    # Sample courses
    courses = [
        {
            "code": "CS101",
            "name": "Introduction to Computer Science",
            "description": "Basic programming concepts and problem solving",
        },
        {
            "code": "CS201",
            "name": "Data Structures",
            "description": "Arrays, linked lists, stacks, queues, trees, and graphs",
        },
        {
            "code": "CS301",
            "name": "Algorithms",
            "description": "Design and analysis of algorithms",
        },
        {
            "code": "MATH101",
            "name": "Calculus I",
            "description": "Limits, derivatives, and integrals",
        },
        {
            "code": "MATH201",
            "name": "Calculus II",
            "description": "Integration techniques and series",
        },
        {
            "code": "PHYS101",
            "name": "Physics I",
            "description": "Mechanics, thermodynamics, and waves",
        },
        {
            "code": "ENG101",
            "name": "English Composition",
            "description": "Academic writing and critical thinking",
        },
        {
            "code": "HIST101",
            "name": "World History",
            "description": "Survey of world civilizations",
        },
    ]

    # Sample sections for courses
    sections = [
        {
            "course_code": "CS101",
            "section_code": "001",
            "schedule": "MWF 9:00-10:00",
            "capacity": 30,
            "instructor": "Dr. Smith",
            "seats_taken": 15,
        },
        {
            "course_code": "CS101",
            "section_code": "002",
            "schedule": "TTh 2:00-3:30",
            "capacity": 25,
            "instructor": "Dr. Johnson",
            "seats_taken": 20,
        },
        {
            "course_code": "CS201",
            "section_code": "001",
            "schedule": "MWF 11:00-12:00",
            "capacity": 25,
            "instructor": "Dr. Brown",
            "seats_taken": 18,
        },
        {
            "course_code": "MATH101",
            "section_code": "001",
            "schedule": "MWF 8:00-9:00",
            "capacity": 35,
            "instructor": "Dr. Davis",
            "seats_taken": 28,
        },
        {
            "course_code": "MATH101",
            "section_code": "002",
            "schedule": "TTh 10:00-11:30",
            "capacity": 30,
            "instructor": "Dr. Wilson",
            "seats_taken": 22,
        },
        {
            "course_code": "ENG101",
            "section_code": "001",
            "schedule": "MWF 1:00-2:00",
            "capacity": 20,
            "instructor": "Prof. Miller",
            "seats_taken": 16,
        },
    ]

    db: Session = SessionLocal()
    try:
        # Seed personas
        for persona in personas:
            existing = db.query(User).filter_by(username=persona["username"]).first()
            if not existing:
                user = User(**persona)
                db.add(user)

        # Seed courses
        for course_data in courses:
            existing = db.query(Course).filter_by(code=course_data["code"]).first()
            if not existing:
                course = Course(**course_data)
                db.add(course)

        db.commit()

        # Seed sections (after courses are committed to get IDs)
        for section_data in sections:
            course = (
                db.query(Course).filter_by(code=section_data["course_code"]).first()
            )
            if course:
                existing_section = (
                    db.query(Section)
                    .filter_by(
                        course_id=course.id, section_code=section_data["section_code"]
                    )
                    .first()
                )
                if not existing_section:
                    section = Section(
                        course_id=course.id,
                        section_code=section_data["section_code"],
                        schedule=section_data["schedule"],
                        capacity=section_data["capacity"],
                        instructor=section_data["instructor"],
                        seats_taken=section_data["seats_taken"],
                    )
                    db.add(section)

        # Create sample approved enrollment requests for testing (if requested)
        if enroll_sarah:
            print("📚 Creating sample enrollments for Sarah...", flush=True)

            # Get Sarah Ahmed's user ID
            sarah = db.query(User).filter_by(username="sarah.ahmed").first()
            if sarah:
                # Get some courses and sections for enrollment
                cs101 = db.query(Course).filter_by(code="CS101").first()
                math101 = db.query(Course).filter_by(code="MATH101").first()
                eng101 = db.query(Course).filter_by(code="ENG101").first()

                if cs101:
                    cs101_section = (
                        db.query(Section).filter_by(course_id=cs101.id).first()
                    )
                    enrollment1 = Request(
                        student_id=sarah.id,
                        request_type="add",
                        course_id=cs101.id,
                        section_to_id=cs101_section.id if cs101_section else None,
                        justification="Required course for Computer Engineering major",
                        status="approved",
                        advisor_id=db.query(User).filter_by(role="advisor").first().id,
                    )
                    db.add(enrollment1)

                if math101:
                    math101_section = (
                        db.query(Section).filter_by(course_id=math101.id).first()
                    )
                    enrollment2 = Request(
                        student_id=sarah.id,
                        request_type="add",
                        course_id=math101.id,
                        section_to_id=math101_section.id if math101_section else None,
                        justification="Required mathematics course",
                        status="approved",
                        advisor_id=db.query(User).filter_by(role="advisor").first().id,
                    )
                    db.add(enrollment2)

                if eng101:
                    eng101_section = (
                        db.query(Section).filter_by(course_id=eng101.id).first()
                    )
                    enrollment3 = Request(
                        student_id=sarah.id,
                        request_type="add",
                        course_id=eng101.id,
                        section_to_id=eng101_section.id if eng101_section else None,
                        justification="General education requirement",
                        status="approved",
                        advisor_id=db.query(User).filter_by(role="advisor").first().id,
                    )
                    db.add(enrollment3)

                print(
                    f"✅ Created sample enrollments for {sarah.full_name}", flush=True
                )
        else:
            print(
                "📚 Skipping Sarah's enrollments (use --enroll_sarah to create them)",
                flush=True,
            )

        db.commit()
        enrollment_msg = "and enrollments" if enroll_sarah else "(no enrollments)"
        print(
            f"✅ Database seeded successfully with personas, courses {enrollment_msg}",
            flush=True,
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed the database with personas and optionally create Sarah's enrollments"
    )
    parser.add_argument(
        "--enroll_sarah",
        action="store_true",
        help="Create sample approved enrollments for Sarah Ahmed (CS101, MATH101, ENG101)",
    )
    args = parser.parse_args()

    main(enroll_sarah=args.enroll_sarah)
