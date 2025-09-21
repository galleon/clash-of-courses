"""Seed the database with personas defined in the BRS document.

Run this script after database tables have been created (e.g. via
models.Base.metadata.create_all) to populate the users table with
representative personas. The personas correspond to the examples
described in the Business Requirements Specification: three students,
two academic advisors, one department head, and one system administrator.
"""

from sqlalchemy.orm import Session

from db import SessionLocal, engine
from models import User, Base, Course, Section


def main():
    # Create all tables first
    Base.metadata.create_all(bind=engine)

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

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
