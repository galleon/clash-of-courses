"""Test session and schedule conflict detection functionality."""

import uuid
from datetime import datetime, date
from brs_backend.models.database import (
    Campus, Course, Student, Program, Section, Term, Instructor,
    SectionMeeting, CampusRoom, Enrollment
)


class TestSessionConflicts:
    """Test schedule and session conflict detection."""
    
    def test_basic_time_range_conflicts(self, db_session):
        """Test basic TSRANGE conflict detection between course sessions."""
        # Create test data
        campus = Campus(name="Conflict Campus", location="Test Location")
        db_session.add(campus)
        db_session.flush()
        
        course1 = Course(
            code="CS101", title="Intro to CS", credits=3,
            department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
        )
        course2 = Course(
            code="MATH201", title="Calculus", credits=4,
            department_id=uuid.uuid4(), level=200, campus_id=campus.campus_id
        )
        db_session.add_all([course1, course2])
        db_session.flush()
        
        term = Term(
            name="Fall 2024",
            starts_on=date(2024, 9, 1),
            ends_on=date(2024, 12, 15)
        )
        db_session.add(term)
        db_session.flush()
        
        instructor = Instructor(
            name="Prof. Test", department_id=uuid.uuid4(), campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()
        
        room = CampusRoom(name="Room 101", capacity=30, campus_id=campus.campus_id)
        db_session.add(room)
        db_session.flush()
        
        # Create sections
        section1 = Section(
            course_id=course1.course_id, term_id=term.term_id, section_code="A01",
            instructor_id=instructor.instructor_id, capacity=30, campus_id=campus.campus_id
        )
        section2 = Section(
            course_id=course2.course_id, term_id=term.term_id, section_code="B01",
            instructor_id=instructor.instructor_id, capacity=25, campus_id=campus.campus_id
        )
        db_session.add_all([section1, section2])
        db_session.flush()
        
        # Create conflicting meetings - both on Monday at overlapping times
        meeting1 = SectionMeeting(
            section_id=section1.section_id,
            activity="LEC",
            day_of_week=1,  # Monday
            time_range="[2024-01-01 10:00:00,2024-01-01 11:30:00)",
            room_id=room.room_id
        )
        meeting2 = SectionMeeting(
            section_id=section2.section_id,
            activity="LEC", 
            day_of_week=1,  # Monday
            time_range="[2024-01-01 11:00:00,2024-01-01 12:30:00)",  # Overlaps with meeting1
            room_id=room.room_id
        )
        db_session.add_all([meeting1, meeting2])
        db_session.commit()
        
        # Test conflict detection using PostgreSQL TSRANGE overlap
        from sqlalchemy import text
        conflict_query = text("""
            SELECT 
                m1.section_id as section1_id,
                m2.section_id as section2_id,
                m1.time_range as time1,
                m2.time_range as time2,
                m1.time_range && m2.time_range as has_overlap
            FROM section_meeting m1, section_meeting m2
            WHERE m1.section_id != m2.section_id
            AND m1.day_of_week = m2.day_of_week
            AND m1.time_range && m2.time_range
        """)
        
        conflicts = db_session.execute(conflict_query).fetchall()
        
        # Should detect the conflict
        assert len(conflicts) >= 1
        assert conflicts[0].has_overlap is True
        print(f"✅ Time range conflict detected: {len(conflicts)} conflicts found")

    def test_student_enrollment_conflicts(self, db_session):
        """Test conflict detection when student tries to enroll in conflicting sections."""
        # Create test data
        campus = Campus(name="Enrollment Campus", location="Student Center")
        db_session.add(campus)
        db_session.flush()
        
        program = Program(
            name="Computer Science", max_credits=120, campus_id=campus.campus_id
        )
        db_session.add(program)
        db_session.flush()
        
        student = Student(
            external_sis_id="CONFLICT_STU",
            program_id=program.program_id,
            campus_id=campus.campus_id
        )
        db_session.add(student)
        db_session.flush()
        
        # Create courses
        course1 = Course(
            code="CS150", title="Programming I", credits=3,
            department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
        )
        course2 = Course(
            code="CS250", title="Programming II", credits=3,
            department_id=uuid.uuid4(), level=200, campus_id=campus.campus_id
        )
        db_session.add_all([course1, course2])
        db_session.flush()
        
        term = Term(name="Spring 2024", starts_on=date(2024, 1, 15))
        instructor = Instructor(name="Dr. Code", department_id=uuid.uuid4(), campus_id=campus.campus_id)
        room = CampusRoom(name="Lab 201", capacity=20, campus_id=campus.campus_id)
        db_session.add_all([term, instructor, room])
        db_session.flush()
        
        # Create sections with conflicting times
        section1 = Section(
            course_id=course1.course_id, term_id=term.term_id, section_code="L01",
            instructor_id=instructor.instructor_id, capacity=20, campus_id=campus.campus_id
        )
        section2 = Section(
            course_id=course2.course_id, term_id=term.term_id, section_code="L02",
            instructor_id=instructor.instructor_id, capacity=20, campus_id=campus.campus_id
        )
        db_session.add_all([section1, section2])
        db_session.flush()
        
        # Student is already enrolled in section1
        enrollment1 = Enrollment(
            student_id=student.student_id,
            section_id=section1.section_id,
            status="registered"
        )
        db_session.add(enrollment1)
        
        # Create meetings - conflicting times
        meeting1 = SectionMeeting(
            section_id=section1.section_id,
            activity="LAB",
            day_of_week=2,  # Tuesday
            time_range="[2024-01-01 14:00:00,2024-01-01 16:00:00)",
            room_id=room.room_id
        )
        meeting2 = SectionMeeting(
            section_id=section2.section_id,
            activity="LAB",
            day_of_week=2,  # Tuesday  
            time_range="[2024-01-01 15:00:00,2024-01-01 17:00:00)",  # Conflicts with meeting1
            room_id=room.room_id
        )
        db_session.add_all([meeting1, meeting2])
        db_session.commit()
        
        # Check if student has enrollment conflicts
        from sqlalchemy import text
        student_conflict_query = text("""
            WITH student_schedule AS (
                SELECT sm.day_of_week, sm.time_range, sm.section_id
                FROM enrollment e
                JOIN section_meeting sm ON sm.section_id = e.section_id
                WHERE e.student_id = :student_id AND e.status = 'registered'
            ),
            potential_conflict AS (
                SELECT sm.day_of_week, sm.time_range, sm.section_id
                FROM section_meeting sm
                WHERE sm.section_id = :new_section_id
            )
            SELECT 
                ss.section_id as existing_section,
                pc.section_id as new_section,
                ss.time_range && pc.time_range as has_conflict
            FROM student_schedule ss, potential_conflict pc
            WHERE ss.day_of_week = pc.day_of_week
            AND ss.time_range && pc.time_range
        """)
        
        conflicts = db_session.execute(student_conflict_query, {
            "student_id": str(student.student_id),
            "new_section_id": str(section2.section_id)
        }).fetchall()
        
        assert len(conflicts) == 1
        assert conflicts[0].has_conflict is True
        print(f"✅ Student enrollment conflict detected: existing section conflicts with new section")

    def test_room_double_booking_conflicts(self, db_session):
        """Test detection of room double-booking conflicts."""
        # Create test data
        campus = Campus(name="Room Campus", location="Academic Building")
        db_session.add(campus)
        db_session.flush()
        
        # Single room that will be double-booked
        room = CampusRoom(name="Conference Room", capacity=50, campus_id=campus.campus_id)
        db_session.add(room)
        db_session.flush()
        
        course1 = Course(
            code="BUSI101", title="Business Ethics", credits=3,
            department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
        )
        course2 = Course(
            code="BUSI201", title="Marketing", credits=3,
            department_id=uuid.uuid4(), level=200, campus_id=campus.campus_id
        )
        db_session.add_all([course1, course2])
        db_session.flush()
        
        term = Term(name="Summer 2024")
        instructor1 = Instructor(name="Prof. Ethics", department_id=uuid.uuid4(), campus_id=campus.campus_id)
        instructor2 = Instructor(name="Prof. Marketing", department_id=uuid.uuid4(), campus_id=campus.campus_id)
        db_session.add_all([term, instructor1, instructor2])
        db_session.flush()
        
        section1 = Section(
            course_id=course1.course_id, term_id=term.term_id, section_code="E01",
            instructor_id=instructor1.instructor_id, capacity=30, campus_id=campus.campus_id
        )
        section2 = Section(
            course_id=course2.course_id, term_id=term.term_id, section_code="M01", 
            instructor_id=instructor2.instructor_id, capacity=35, campus_id=campus.campus_id
        )
        db_session.add_all([section1, section2])
        db_session.flush()
        
        # Both sections try to use the same room at the same time
        meeting1 = SectionMeeting(
            section_id=section1.section_id,
            activity="LEC",
            day_of_week=3,  # Wednesday
            time_range="[2024-01-01 09:00:00,2024-01-01 10:30:00)",
            room_id=room.room_id
        )
        meeting2 = SectionMeeting(
            section_id=section2.section_id,
            activity="LEC",
            day_of_week=3,  # Wednesday
            time_range="[2024-01-01 09:30:00,2024-01-01 11:00:00)",  # Overlapping time
            room_id=room.room_id  # Same room!
        )
        db_session.add_all([meeting1, meeting2])
        db_session.commit()
        
        # Detect room double-booking
        from sqlalchemy import text
        room_conflict_query = text("""
            SELECT 
                m1.section_id as section1,
                m2.section_id as section2,
                r.name as room_name,
                m1.time_range as time1,
                m2.time_range as time2
            FROM section_meeting m1
            JOIN section_meeting m2 ON (
                m1.room_id = m2.room_id 
                AND m1.section_id != m2.section_id
                AND m1.day_of_week = m2.day_of_week
                AND m1.time_range && m2.time_range
            )
            JOIN campus_room r ON r.room_id = m1.room_id
        """)
        
        room_conflicts = db_session.execute(room_conflict_query).fetchall()
        
        assert len(room_conflicts) >= 1
        assert room_conflicts[0].room_name == "Conference Room"
        print(f"✅ Room double-booking detected: {room_conflicts[0].room_name} has {len(room_conflicts)} conflicts")

    def test_instructor_schedule_conflicts(self, db_session):
        """Test detection of instructor teaching multiple sections at the same time."""
        # Create test data
        campus = Campus(name="Instructor Campus", location="Faculty Building")  
        db_session.add(campus)
        db_session.flush()
        
        # One instructor teaching multiple courses
        instructor = Instructor(
            name="Dr. Overbooked", department_id=uuid.uuid4(), campus_id=campus.campus_id
        )
        db_session.add(instructor)
        db_session.flush()
        
        course1 = Course(
            code="PHYS101", title="Physics I", credits=4,
            department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
        )
        course2 = Course(
            code="PHYS102", title="Physics II", credits=4,
            department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
        )
        db_session.add_all([course1, course2])
        db_session.flush()
        
        term = Term(name="Fall 2024")
        room1 = CampusRoom(name="Physics Lab 1", capacity=24, campus_id=campus.campus_id)
        room2 = CampusRoom(name="Physics Lab 2", capacity=24, campus_id=campus.campus_id)
        db_session.add_all([term, room1, room2])
        db_session.flush()
        
        # Same instructor assigned to both sections
        section1 = Section(
            course_id=course1.course_id, term_id=term.term_id, section_code="P01",
            instructor_id=instructor.instructor_id, capacity=20, campus_id=campus.campus_id
        )
        section2 = Section(
            course_id=course2.course_id, term_id=term.term_id, section_code="P02",
            instructor_id=instructor.instructor_id, capacity=20, campus_id=campus.campus_id
        )
        db_session.add_all([section1, section2])
        db_session.flush()
        
        # Conflicting meeting times for same instructor
        meeting1 = SectionMeeting(
            section_id=section1.section_id,
            activity="LAB",
            day_of_week=4,  # Thursday
            time_range="[2024-01-01 13:00:00,2024-01-01 15:00:00)",
            room_id=room1.room_id
        )
        meeting2 = SectionMeeting(
            section_id=section2.section_id,
            activity="LAB", 
            day_of_week=4,  # Thursday
            time_range="[2024-01-01 14:00:00,2024-01-01 16:00:00)",  # Overlaps
            room_id=room2.room_id
        )
        db_session.add_all([meeting1, meeting2])
        db_session.commit()
        
        # Detect instructor scheduling conflicts
        from sqlalchemy import text
        instructor_conflict_query = text("""
            SELECT 
                i.name as instructor_name,
                s1.section_code as section1_code,
                s2.section_code as section2_code,
                m1.time_range as time1,
                m2.time_range as time2
            FROM section s1
            JOIN section s2 ON (
                s1.instructor_id = s2.instructor_id 
                AND s1.section_id != s2.section_id
            )
            JOIN section_meeting m1 ON m1.section_id = s1.section_id
            JOIN section_meeting m2 ON (
                m2.section_id = s2.section_id
                AND m1.day_of_week = m2.day_of_week
                AND m1.time_range && m2.time_range
            )
            JOIN instructor i ON i.instructor_id = s1.instructor_id
        """)
        
        instructor_conflicts = db_session.execute(instructor_conflict_query).fetchall()
        
        assert len(instructor_conflicts) >= 1
        assert instructor_conflicts[0].instructor_name == "Dr. Overbooked"
        print(f"✅ Instructor scheduling conflict detected: {instructor_conflicts[0].instructor_name} double-booked")

    def test_comprehensive_conflict_analysis(self, db_session):
        """Test comprehensive conflict analysis across all dimensions."""
        # Create a complex scenario with multiple types of conflicts
        campus = Campus(name="Complex Campus", location="University Center")
        db_session.add(campus)
        db_session.flush()
        
        # Create multiple courses, instructors, rooms
        courses = []
        for i in range(3):
            course = Course(
                code=f"TEST{i+1}01", title=f"Test Course {i+1}", credits=3,
                department_id=uuid.uuid4(), level=100, campus_id=campus.campus_id
            )
            courses.append(course)
            db_session.add(course)
        
        instructors = []
        for i in range(2):
            instructor = Instructor(
                name=f"Prof. Test{i+1}", department_id=uuid.uuid4(), campus_id=campus.campus_id
            )
            instructors.append(instructor)
            db_session.add(instructor)
            
        rooms = []
        for i in range(2):
            room = CampusRoom(
                name=f"Room {i+1}01", capacity=30, campus_id=campus.campus_id
            )
            rooms.append(room)
            db_session.add(room)
            
        term = Term(name="Conflict Term")
        db_session.add(term)
        db_session.flush()
        
        # Create sections with various conflicts
        sections = []
        for i, course in enumerate(courses):
            section = Section(
                course_id=course.course_id, term_id=term.term_id, 
                section_code=f"C0{i+1}",
                instructor_id=instructors[i % 2].instructor_id,  # Some instructors teach multiple
                capacity=25, campus_id=campus.campus_id
            )
            sections.append(section)
            db_session.add(section)
        db_session.flush()
        
        # Create meetings with intentional conflicts
        meeting_configs = [
            (0, 1, "[2024-01-01 10:00:00,2024-01-01 11:30:00)", 0),  # Section 0, Monday, Room 0
            (1, 1, "[2024-01-01 11:00:00,2024-01-01 12:30:00)", 0),  # Section 1, Monday, Room 0 (room conflict)
            (2, 1, "[2024-01-01 10:30:00,2024-01-01 12:00:00)", 1),  # Section 2, Monday, Room 1 (instructor conflict with section 0)
        ]
        
        meetings = []
        for section_idx, day, time_range, room_idx in meeting_configs:
            meeting = SectionMeeting(
                section_id=sections[section_idx].section_id,
                activity="LEC",
                day_of_week=day,
                time_range=time_range,
                room_id=rooms[room_idx].room_id
            )
            meetings.append(meeting)
            db_session.add(meeting)
        db_session.commit()
        
        # Comprehensive conflict analysis
        from sqlalchemy import text
        all_conflicts_query = text("""
            WITH conflict_analysis AS (
                SELECT 
                    'ROOM' as conflict_type,
                    m1.section_id as section1,
                    m2.section_id as section2,
                    r.name as resource_name,
                    m1.time_range && m2.time_range as has_overlap
                FROM section_meeting m1
                JOIN section_meeting m2 ON (
                    m1.room_id = m2.room_id 
                    AND m1.section_id != m2.section_id
                    AND m1.day_of_week = m2.day_of_week
                    AND m1.time_range && m2.time_range
                )
                JOIN campus_room r ON r.room_id = m1.room_id
                
                UNION ALL
                
                SELECT 
                    'INSTRUCTOR' as conflict_type,
                    s1.section_id as section1,
                    s2.section_id as section2,
                    i.name as resource_name,
                    m1.time_range && m2.time_range as has_overlap
                FROM section s1
                JOIN section s2 ON (
                    s1.instructor_id = s2.instructor_id 
                    AND s1.section_id != s2.section_id
                )
                JOIN section_meeting m1 ON m1.section_id = s1.section_id
                JOIN section_meeting m2 ON (
                    m2.section_id = s2.section_id
                    AND m1.day_of_week = m2.day_of_week
                    AND m1.time_range && m2.time_range
                )
                JOIN instructor i ON i.instructor_id = s1.instructor_id
            )
            SELECT 
                conflict_type,
                COUNT(*) as conflict_count,
                ARRAY_AGG(DISTINCT resource_name) as conflicted_resources
            FROM conflict_analysis
            WHERE has_overlap = true
            GROUP BY conflict_type
        """)
        
        conflict_summary = db_session.execute(all_conflicts_query).fetchall()
        
        # Should detect both room and instructor conflicts
        conflict_types = {row.conflict_type: row.conflict_count for row in conflict_summary}
        
        assert 'ROOM' in conflict_types
        assert 'INSTRUCTOR' in conflict_types
        assert conflict_types['ROOM'] >= 1
        assert conflict_types['INSTRUCTOR'] >= 1
        
        print(f"✅ Comprehensive conflict analysis complete:")
        for row in conflict_summary:
            print(f"   {row.conflict_type}: {row.conflict_count} conflicts ({row.conflicted_resources})")