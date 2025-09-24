-- BRS V2 Database Schema Migration
-- Enhanced academic modeling with prerequisites, sections, and calendar integration

BEGIN TRANSACTION;

-- ==========================
-- CORE IDENTITY & ORGANIZATION
-- ==========================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enhanced student table
CREATE TABLE student_v2(
  student_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  external_sis_id TEXT UNIQUE,
  full_name TEXT NOT NULL,
  email TEXT UNIQUE,
  program_id UUID, -- Will reference program table
  major TEXT, -- Keep for backward compatibility
  standing TEXT NOT NULL DEFAULT 'regular' CHECK (standing IN ('regular','probation','suspended')),
  gpa NUMERIC(3,2),
  credits_completed INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enhanced course table with academic rigor
CREATE TABLE course_v2(
  course_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  code TEXT NOT NULL UNIQUE,           -- e.g., CS101
  title TEXT NOT NULL,
  description TEXT,
  credits INT NOT NULL,
  department_id UUID, -- Will reference department table
  level INT NOT NULL,            -- 100/200/300/400
  prerequisites TEXT, -- JSON array for complex prereq logic
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Prerequisites and corequisites
CREATE TABLE course_prereq(
  course_id UUID REFERENCES course_v2(course_id) ON DELETE CASCADE,
  req_course_id UUID REFERENCES course_v2(course_id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('prereq','coreq','equivalency')),
  minimum_grade TEXT DEFAULT 'D', -- C-, C, C+, B-, etc.
  PRIMARY KEY(course_id, req_course_id, type)
);

-- Academic terms
CREATE TABLE term(
  term_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL UNIQUE,                    -- e.g., 2025-Fall
  starts_on DATE NOT NULL, 
  ends_on DATE NOT NULL,
  registration_opens TIMESTAMPTZ,
  registration_closes TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT false
);

-- ==========================
-- SECTIONS & SCHEDULING
-- ==========================

-- Course sections per term
CREATE TABLE section(
  section_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  course_id UUID REFERENCES course_v2(course_id) ON DELETE CASCADE,
  term_id UUID REFERENCES term(term_id) ON DELETE CASCADE,
  section_code TEXT NOT NULL,            -- e.g., A1, B2
  instructor_name TEXT, -- Simplified for now
  capacity INT NOT NULL DEFAULT 25,
  waitlist_capacity INT DEFAULT 5,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(course_id, term_id, section_code)
);

-- Individual meeting times for each section
CREATE TABLE section_meeting(
  meeting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  section_id UUID REFERENCES section(section_id) ON DELETE CASCADE,
  activity TEXT NOT NULL DEFAULT 'LEC' CHECK (activity IN ('LEC','LAB','TUT','SEM')),
  day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Monday
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  room TEXT,
  CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Optimized indices for conflict detection
CREATE INDEX idx_section_meeting_section ON section_meeting(section_id);
CREATE INDEX idx_section_meeting_schedule ON section_meeting(day_of_week, start_time, end_time);

-- ==========================
-- ENROLLMENT & REQUESTS
-- ==========================

-- Student enrollments
CREATE TABLE enrollment(
  enrollment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  section_id UUID REFERENCES section(section_id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'registered' CHECK (status IN ('registered','waitlisted','dropped')),
  enrolled_at TIMESTAMPTZ DEFAULT now(),
  dropped_at TIMESTAMPTZ,
  UNIQUE(student_id, section_id)
);

-- Enhanced registration requests
CREATE TABLE registration_request_v2(
  request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('ADD','DROP','CHANGE_SECTION')),
  from_section_id UUID NULL REFERENCES section(section_id), -- for DROP/CHANGE
  to_section_id   UUID NULL REFERENCES section(section_id), -- for ADD/CHANGE
  justification TEXT,
  state TEXT NOT NULL DEFAULT 'submitted' CHECK (state IN ('submitted','advisor_review','dept_review','approved','rejected','cancelled')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Decision tracking
CREATE TABLE request_decision(
  decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID REFERENCES registration_request_v2(request_id) ON DELETE CASCADE,
  actor_role TEXT CHECK (actor_role IN ('advisor','department_head','system')),
  actor_id UUID, -- References user who made decision
  action TEXT CHECK (action IN ('approve','reject','refer','hold')),
  rationale TEXT,
  decided_at TIMESTAMPTZ DEFAULT now()
);

-- Rule violations and conflicts
CREATE TABLE request_conflict(
  conflict_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id UUID REFERENCES registration_request_v2(request_id) ON DELETE CASCADE,
  rule_code TEXT NOT NULL,         -- e.g., BR-005 time conflict, BR-003 credit cap
  severity TEXT CHECK (severity IN ('error','warning','info')) DEFAULT 'error',
  description TEXT,
  details JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================
-- CALENDAR INTEGRATION
-- ==========================

-- Canonical calendar events
CREATE TABLE calendar_event(
  event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  source TEXT NOT NULL DEFAULT 'system' CHECK (source IN ('system','external','manual')),
  title TEXT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL,
  ends_at TIMESTAMPTZ NOT NULL,
  location TEXT,
  external_id TEXT, -- For syncing with external calendars
  payload JSONB,    -- ICS fields, zoom links, etc.
  created_at TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT valid_event_time CHECK (ends_at > starts_at)
);

-- Links events to academic objects
CREATE TABLE calendar_binding(
  binding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID REFERENCES calendar_event(event_id) ON DELETE CASCADE,
  section_id UUID NULL REFERENCES section(section_id),
  meeting_id UUID NULL REFERENCES section_meeting(meeting_id),
  UNIQUE(event_id, section_id, meeting_id)
);

-- ==========================
-- PREFERENCES & RECOMMENDATIONS
-- ==========================

-- Explicit student preferences
CREATE TABLE student_preference(
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  preference_key TEXT NOT NULL, 
  preference_value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY(student_id, preference_key)
);

-- Implicit behavioral signals
CREATE TABLE student_signal(
  signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  signal_type TEXT NOT NULL,                 -- e.g., "like_timeslot","dislike_instructor"
  signal_value JSONB NOT NULL,
  weight NUMERIC(3,2) DEFAULT 1.0, -- Signal strength
  created_at TIMESTAMPTZ DEFAULT now()
);

-- AI-generated recommendations
CREATE TABLE recommendation(
  rec_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  kind TEXT CHECK (kind IN ('add_course','swap_section','drop_course','optimize_schedule')),
  proposal JSONB NOT NULL,                   -- Structured change set
  features JSONB,                           -- Model inputs and scores
  confidence_score NUMERIC(3,2),           -- 0.00 to 1.00
  explanation TEXT,                         -- Natural language reasoning
  created_at TIMESTAMPTZ DEFAULT now()
);

-- User feedback on recommendations
CREATE TABLE recommendation_feedback(
  rec_id UUID REFERENCES recommendation(rec_id) ON DELETE CASCADE,
  student_id UUID REFERENCES student_v2(student_id) ON DELETE CASCADE,
  feedback TEXT CHECK (feedback IN ('accept','reject','later','thumbs_up','thumbs_down')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY(rec_id, student_id)
);

-- ==========================
-- AUDIT & COMPLIANCE
-- ==========================

-- Comprehensive audit trail
CREATE TABLE audit_log(
  audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
  old_values JSONB,
  new_values JSONB,
  user_id UUID,
  user_role TEXT,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================
-- VIEWS FOR COMMON QUERIES
-- ==========================

-- Student current schedule for active term
CREATE VIEW student_current_schedule AS
SELECT 
    s.student_id,
    s.full_name,
    c.code as course_code,
    c.title as course_title,
    c.credits,
    sec.section_code,
    sec.instructor_name,
    sm.day_of_week,
    sm.start_time,
    sm.end_time,
    sm.room,
    sm.activity
FROM student_v2 s
JOIN enrollment e ON s.student_id = e.student_id
JOIN section sec ON e.section_id = sec.section_id
JOIN course_v2 c ON sec.course_id = c.course_id
JOIN section_meeting sm ON sec.section_id = sm.section_id
JOIN term t ON sec.term_id = t.term_id
WHERE e.status = 'registered' 
  AND t.is_active = true;

-- Student schedule conflicts view
CREATE VIEW schedule_conflicts AS
SELECT DISTINCT
    sm1.section_id as section1,
    sm2.section_id as section2,
    sm1.day_of_week,
    sm1.start_time as start1,
    sm1.end_time as end1,
    sm2.start_time as start2,
    sm2.end_time as end2
FROM section_meeting sm1
JOIN section_meeting sm2 ON sm1.day_of_week = sm2.day_of_week
WHERE sm1.section_id < sm2.section_id  -- Avoid duplicate pairs
  AND (sm1.start_time, sm1.end_time) OVERLAPS (sm2.start_time, sm2.end_time);

COMMIT;