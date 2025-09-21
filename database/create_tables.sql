-- SQL schema for the BRS prototype
-- Users table holds all user accounts with a role indicating their persona.
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(30) NOT NULL CHECK (role IN ('student','advisor','department_head','system_admin')),
    age INTEGER,
    gender VARCHAR(10),
    major VARCHAR(100),
    gpa DECIMAL(3,2),
    credit_hours_completed INTEGER,
    technology_proficiency VARCHAR(50),
    description TEXT
);

-- Courses table holds a catalog of courses available in the system.
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Sections represent specific offerings of a course, including schedule and capacity.
CREATE TABLE IF NOT EXISTS sections (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    section_code VARCHAR(20) NOT NULL,
    schedule VARCHAR(100),
    capacity INTEGER,
    instructor VARCHAR(100),
    seats_taken INTEGER DEFAULT 0,
    UNIQUE(course_id, section_code)
);

-- Requests table tracks add/drop/section change requests submitted by students.
CREATE TABLE IF NOT EXISTS requests (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    request_type VARCHAR(20) NOT NULL CHECK (request_type IN ('add','drop','change')),
    course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    section_from_id INTEGER REFERENCES sections(id) ON DELETE SET NULL,
    section_to_id INTEGER REFERENCES sections(id) ON DELETE SET NULL,
    justification TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','referred')),
    advisor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    department_head_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);