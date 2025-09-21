"""SQLAlchemy models for the BRS prototype.

This module defines ORM models corresponding to the database schema
defined in the SQL migrations. Each class represents a table in the
database with relationships where appropriate.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))
    major = Column(String(100))
    gpa = Column(DECIMAL(3, 2))
    credit_hours_completed = Column(Integer)
    technology_proficiency = Column(String(50))
    description = Column(Text)

    # relationships
    requests = relationship(
        "Request", back_populates="student", foreign_keys="Request.student_id"
    )
    advisor_requests = relationship(
        "Request", back_populates="advisor", foreign_keys="Request.advisor_id"
    )
    head_requests = relationship(
        "Request",
        back_populates="department_head",
        foreign_keys="Request.department_head_id",
    )


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    sections = relationship(
        "Section", back_populates="course", cascade="all, delete-orphan"
    )
    requests = relationship("Request", back_populates="course")


class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    section_code = Column(String(20), nullable=False)
    schedule = Column(String(100))
    capacity = Column(Integer)
    instructor = Column(String(100))
    seats_taken = Column(Integer, default=0)

    course = relationship("Course", back_populates="sections")
    requests_from = relationship(
        "Request", back_populates="section_from", foreign_keys="Request.section_from_id"
    )
    requests_to = relationship(
        "Request", back_populates="section_to", foreign_keys="Request.section_to_id"
    )


class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    request_type = Column(String(20), nullable=False)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    section_from_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"))
    section_to_id = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"))
    justification = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    advisor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    department_head_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    # relationships
    student = relationship("User", back_populates="requests", foreign_keys=[student_id])
    advisor = relationship(
        "User", back_populates="advisor_requests", foreign_keys=[advisor_id]
    )
    department_head = relationship(
        "User", back_populates="head_requests", foreign_keys=[department_head_id]
    )
    course = relationship("Course", back_populates="requests")
    section_from = relationship(
        "Section", foreign_keys=[section_from_id], back_populates="requests_from"
    )
    section_to = relationship(
        "Section", foreign_keys=[section_to_id], back_populates="requests_to"
    )
