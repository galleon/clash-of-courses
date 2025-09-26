--
-- create_tables.sql
--
-- This script defines the database schema for the Student Course
-- Management system with extensions to meet the new requirements.  It
-- creates core tables such as student, course, section and
-- registration_request, and adds new tables (campus, program,
-- instructor, campus_room) along with additional columns for financial
-- status, study type, student status, delivery mode and campus
-- affiliation.  Indexes are provided to support efficient time
-- conflict checks.

-- --------------------------------------------------------------------
-- Campus and program metadata
-- --------------------------------------------------------------------
CREATE TABLE campus (
    campus_id UUID PRIMARY KEY,
    name      TEXT NOT NULL,
    location  TEXT
);

CREATE TABLE program (
    program_id  UUID PRIMARY KEY,
    name        TEXT NOT NULL,
    max_credits INT NOT NULL,
    campus_id   UUID REFERENCES campus(campus_id)
);

-- --------------------------------------------------------------------
-- Term definition with registration window
-- --------------------------------------------------------------------
CREATE TABLE term (
    term_id                UUID PRIMARY KEY,
    name                   TEXT,
    starts_on              DATE,
    ends_on                DATE,
    registration_starts_on DATE,
    registration_ends_on   DATE
);

-- --------------------------------------------------------------------
-- Student information
-- Additional fields: financial_status, study_type, student_status,
-- expected_grad_term and campus_id.  The student_status field
-- distinguishes new students, those following a plan, those expected
-- to graduate, and struggling students.  financial_status and
-- study_type support the paid/free and scholarship requirements.
-- --------------------------------------------------------------------
CREATE TABLE student (
    student_id         UUID PRIMARY KEY,
    external_sis_id    TEXT UNIQUE,
    program_id         UUID REFERENCES program(program_id),
    campus_id          UUID REFERENCES campus(campus_id),
    standing           TEXT NOT NULL CHECK (standing IN ('regular','probation','suspended')),
    student_status     TEXT CHECK (student_status IN ('new','following_plan','expected_graduate','struggling')),
    gpa                NUMERIC(3,2),
    credits_completed  INT NOT NULL DEFAULT 0,
    financial_status   TEXT CHECK (financial_status IN ('clear','owed','exempt')),
    study_type         TEXT CHECK (study_type IN ('paid','free','scholarship')),
    expected_grad_term UUID NULL REFERENCES term(term_id)
);

-- --------------------------------------------------------------------
-- Course catalog
-- New columns: course_type, semester_pattern, delivery_mode and
-- campus_id.  course_type distinguishes major/university/elective
-- requirements.  semester_pattern records whether the course is
-- offered in odd, even or both semesters.  delivery_mode
-- distinguishes in-person, online and hybrid delivery.
-- --------------------------------------------------------------------
CREATE TABLE course (
    course_id       UUID PRIMARY KEY,
    code            TEXT NOT NULL,
    title           TEXT NOT NULL,
    credits         INT NOT NULL,
    department_id   UUID NOT NULL,
    level           INT NOT NULL,
    course_type     TEXT CHECK (course_type IN ('major','university','elective')),
    semester_pattern TEXT CHECK (semester_pattern IN ('odd','even','both')),
    delivery_mode   TEXT CHECK (delivery_mode IN ('in_person','online','hybrid')),
    campus_id       UUID REFERENCES campus(campus_id)
);

-- Relationship table for prerequisites and corequisites
CREATE TABLE course_prereq (
    course_id    UUID REFERENCES course(course_id),
    req_course_id UUID REFERENCES course(course_id),
    type         TEXT NOT NULL CHECK (type IN ('prereq','coreq','equivalency')),
    PRIMARY KEY (course_id, req_course_id, type)
);

-- --------------------------------------------------------------------
-- Classroom inventory
-- Each room belongs to a campus and has a capacity.  The section
-- meeting table references a room rather than storing a free-form
-- string.
-- --------------------------------------------------------------------
CREATE TABLE campus_room (
    room_id   UUID PRIMARY KEY,
    campus_id UUID REFERENCES campus(campus_id),
    name      TEXT NOT NULL,
    capacity  INT NOT NULL
);

-- --------------------------------------------------------------------
-- Instructor and schedule
-- The instructor table stores basic instructor data.  The
-- instructor_schedule table allows blocking out unavailable times so
-- that the scheduling system can avoid assigning overlapping sections.
-- --------------------------------------------------------------------
CREATE TABLE instructor (
    instructor_id UUID PRIMARY KEY,
    name          TEXT NOT NULL,
    department_id UUID NOT NULL,
    campus_id     UUID REFERENCES campus(campus_id)
);

CREATE TABLE instructor_schedule (
    instructor_id UUID REFERENCES instructor(instructor_id),
    day_of_week   INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    time_range    TSRANGE NOT NULL,
    PRIMARY KEY (instructor_id, day_of_week, time_range)
);

-- --------------------------------------------------------------------
-- Sections and meetings
-- Each section belongs to a course, term and campus.  Meetings are
-- stored separately and reference a campus room.
-- --------------------------------------------------------------------
CREATE TABLE section (
    section_id       UUID PRIMARY KEY,
    course_id        UUID REFERENCES course(course_id),
    term_id          UUID REFERENCES term(term_id),
    section_code     TEXT,
    instructor_id    UUID REFERENCES instructor(instructor_id),
    capacity         INT NOT NULL,
    waitlist_capacity INT DEFAULT 0,
    campus_id        UUID REFERENCES campus(campus_id),
    UNIQUE (course_id, term_id, section_code)
);

CREATE TABLE section_meeting (
    meeting_id UUID PRIMARY KEY,
    section_id UUID REFERENCES section(section_id) ON DELETE CASCADE,
    activity   TEXT NOT NULL CHECK (activity IN ('LEC','LAB','TUT')),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    time_range TSRANGE NOT NULL,
    room_id    UUID REFERENCES campus_room(room_id)
);

-- GiST index to accelerate overlap queries for conflict detection
CREATE INDEX section_meeting_section_id_idx ON section_meeting (section_id);
CREATE INDEX section_meeting_tr_gist ON section_meeting USING GIST (day_of_week, time_range);

-- --------------------------------------------------------------------
-- Enrollment table
-- --------------------------------------------------------------------
CREATE TABLE enrollment (
    enrollment_id UUID PRIMARY KEY,
    student_id    UUID REFERENCES student(student_id),
    section_id    UUID REFERENCES section(section_id),
    status        TEXT NOT NULL CHECK (status IN ('registered','waitlisted','dropped')),
    enrolled_at   TIMESTAMPTZ DEFAULT now(),
    UNIQUE (student_id, section_id)
);

-- --------------------------------------------------------------------
-- Registration request workflow
-- Requests model ADD/DROP/CHANGE_SECTION changes.  Decision
-- rationale and conflicts are stored in separate tables.
-- --------------------------------------------------------------------
CREATE TABLE registration_request (
    request_id        UUID PRIMARY KEY,
    student_id        UUID REFERENCES student(student_id),
    type              TEXT NOT NULL CHECK (type IN ('ADD','DROP','CHANGE_SECTION')),
    from_section_id   UUID NULL REFERENCES section(section_id),
    to_section_id     UUID NULL REFERENCES section(section_id),
    reason            TEXT,
    state             TEXT NOT NULL CHECK (state IN ('submitted','advisor_review','dept_review','approved','rejected','cancelled')),
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE request_decision (
    decision_id UUID PRIMARY KEY,
    request_id  UUID REFERENCES registration_request(request_id) ON DELETE CASCADE,
    actor_role  TEXT CHECK (actor_role IN ('advisor','department_head')),
    action      TEXT CHECK (action IN ('approve','reject','refer','hold')),
    rationale   TEXT,
    decided_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE request_conflict (
    id        BIGSERIAL PRIMARY KEY,
    request_id UUID REFERENCES registration_request(request_id) ON DELETE CASCADE,
    rule_code  TEXT,
    details    JSONB
);

-- --------------------------------------------------------------------
-- Calendar events and bindings
-- --------------------------------------------------------------------
CREATE TABLE calendar_event (
    event_id  UUID PRIMARY KEY,
    student_id UUID REFERENCES student(student_id),
    source    TEXT NOT NULL CHECK (source IN ('system','external')),
    title     TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at   TIMESTAMPTZ NOT NULL,
    location  TEXT,
    payload   JSONB
);

CREATE TABLE calendar_binding (
    binding_id UUID PRIMARY KEY,
    event_id   UUID REFERENCES calendar_event(event_id) ON DELETE CASCADE,
    section_id UUID NULL REFERENCES section(section_id),
    meeting_id UUID NULL REFERENCES section_meeting(meeting_id),
    UNIQUE (event_id, section_id, meeting_id)
);

-- --------------------------------------------------------------------
-- Preferences, signals and recommendations
-- --------------------------------------------------------------------
CREATE TABLE student_preference (
    student_id UUID REFERENCES student(student_id),
    key        TEXT,
    value      JSONB,
    PRIMARY KEY (student_id, key)
);

CREATE TABLE student_signal (
    id         BIGSERIAL PRIMARY KEY,
    student_id UUID REFERENCES student(student_id),
    signal_type TEXT,
    signal_value JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recommendation (
    rec_id     UUID PRIMARY KEY,
    student_id UUID REFERENCES student(student_id),
    kind       TEXT CHECK (kind IN ('add_course','swap_section','cancel_course')),
    proposal   JSONB,
    features   JSONB,
    score      DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recommendation_feedback (
    rec_id     UUID REFERENCES recommendation(rec_id) ON DELETE CASCADE,
    student_id UUID REFERENCES student(student_id),
    feedback   TEXT CHECK (feedback IN ('accept','reject','later','thumbs_up','thumbs_down')),
    PRIMARY KEY (rec_id, student_id)
);

-- End of schema definitions
