# Test Scenario: Successfully Tested End-to-End Workflow

This document outlines the successfully tested scenario that demonstrates
the complete course registration workflow with conflict detection and 
automatic alternative enrollment. The system has been validated to work
properly with the following sequence.

## Successfully Tested Scenario

The following scenario has been **successfully tested and validated**:

### 1. Sarah logs in
- User authenticates as Sarah Ahmed (student_id: `4441ab90-e2fe-4da5-a0e1-6a129d61552f`)
- System initializes with baseline schedule

### 2. She requests her current schedule
**Command:** "Show me my current schedule"
- **Expected Result:** Shows ENGR101 S01 in week calendar
- **Actual Result:** ✅ Week grid displays properly with ENGR101 S01 (Monday 10:00-11:30, Wednesday 14:00-15:30)
- **Card Width:** ✅ Week calendar fits properly in container (98% width, no overlap)

### 3. She requests to add ENGR201 section S01
**Command:** "I want to add ENGR201 section S01"
- **Expected Result:** Prerequisite violation (ENGR101 not completed)
- **Actual Result:** ❌ Request rejected - Missing prerequisites: ENGR101
- **Explanation:** Sarah is currently enrolled in ENGR101 S01 but hasn't completed it yet
- **System Response:** Prerequisites must be completed before enrollment

### 4. She requests to add CS101 section S01
**Command:** "I want to add CS101 section S01"
- **Expected Result:** Conflict detected, auto-enrolled in alternative section
- **Actual Result:** ✅ Conflict detected with ENGR101 S01 (Monday overlap), automatically enrolled in CS101 S02
- **Conflict Resolution:** Monday 10:30-12:00 (CS101 S01) conflicts with Monday 10:00-11:30 (ENGR101 S01)
- **Alternative Used:** CS101 S02 (Tuesday 13:00-14:30) - no conflicts

### 5. She requests her current schedule
**Command:** "Show me my current schedule"
- **Expected Result:** Shows ENGR101 and CS101 courses in week calendar
- **Actual Result:** ✅ Week grid displays ENGR101 S01 and CS101 S02
- **Total Credits:** 6 credits across two courses

## System Capabilities Validated

### ✅ Prerequisite Checking
- Properly enforces course prerequisites
- Rejects enrollment when prerequisites not met (ENGR201 requires completed ENGR101)
- Distinguishes between "enrolled in" vs "completed" for prerequisite validation
- Detects time overlaps between course sections
- Identifies specific conflicting time slots (Monday 10:00-11:30 vs 10:30-12:00)

### ✅ Automatic Alternative Enrollment
- Finds non-conflicting alternative sections
- Auto-enrolls student without requiring advisor approval
- Provides clear explanation of conflict and resolution

### ✅ Schedule Display
- Week calendar renders properly with all courses
- No container overlap issues
- Proper day names and time slots displayed

### ✅ Section Code Standardization  
- All sections use consistent Sxx format (S01, S02, S03)
- Proper section identification and scheduling

## Database State After Testing

After the successful scenario execution:
- **ENGR101 S01**: Monday 10:00-11:30, Wednesday 14:00-15:30 (baseline)
- **ENGR201 S01**: ❌ Enrollment rejected due to unmet prerequisites
- **CS101 S02**: Tuesday 13:00-14:30 (alternative auto-enrollment)

Total: 2 courses, 6 credits, no schedule conflicts.

## Key Business Rules Validated

1. **Prerequisite Enforcement**: ENGR201 properly rejected when ENGR101 not completed
2. **Conflict Detection**: CS101 S01 conflict with ENGR101 S01 detected  
3. **Alternative Enrollment**: Automatic enrollment in CS101 S02 when S01 conflicts
4. **Schedule Management**: Clean week calendar display with proper course information
## Original Development Scenario (For Reference)

The following was the original development scenario that guided the implementation:

The database is automatically seeded when you run:

```bash
docker-compose build --no-cache backend && docker-compose up -d backend
```

This runs the `seed_comprehensive` module which creates all tables and
populates them with test data from `seed_personas.py`. The seeding is
idempotent and can be run multiple times safely.

After seeding, the following notable rows exist:

- **Students** – Sarah Ahmed (external_sis_id = 'S1001') is a second-year engineering student with no financial hold, plus additional students for realistic enrollment numbers.
- **Courses** – ENGR101 (Introduction to Engineering) and ENGR201 (Engineering Mechanics), both major courses offered at the main campus.
- **Sections** – four sections are available:
  - A1 and A2 for ENGR101
  - B1 and A2 for ENGR201
- **Meetings** – A1 meets on Monday 10:00–11:30 and Wednesday 2:00–3:30 PM. A2 (ENGR101) meets on Wednesday 2:00–3:15 PM. B1 (ENGR201) meets on Monday 10:30–12:00. A2 (ENGR201) meets on Tuesday 9:30–11:00.
- **Enrollment** – Sarah is already registered in section A1. All sections have realistic enrollment numbers (25-75% capacity).

2. Attempt to add a conflicting course

When Sarah logs in and chooses to add a course, she selects
ENGR201 and chooses section B1.  To simulate this in SQL you
would insert a row into the registration_request table:

```sql
INSERT INTO registration_request
    (request_id, student_id, type, to_section_id, reason, state)
VALUES
    (gen_random_uuid(),
     (SELECT student_id FROM student WHERE external_sis_id = 'S1001'),
     'ADD',
     (SELECT section_id FROM section WHERE section_code = 'B1'),
     'Need to take mechanics next term',
     'submitted');
```

3. Detect the time conflict

To verify the conflict, run the following SQL, which mirrors the
business rule BR‑005.  It checks whether the candidate meeting of the
requested section overlaps with any existing meetings in the
student’s schedule:

```sql
-- Look up the candidate meeting (day and time range) for section B1
WITH candidate AS (
    SELECT sm.day_of_week, sm.time_range
    FROM section_meeting sm
    JOIN section s ON s.section_id = sm.section_id
    WHERE s.section_code = 'B1'
),
busy AS (
    -- meetings for the student’s registered sections
    SELECT sm.day_of_week, sm.time_range
    FROM enrollment e
    JOIN section_meeting sm ON sm.section_id = e.section_id
    WHERE e.student_id = (SELECT student_id FROM student WHERE external_sis_id = 'S1001')
      AND e.status = 'registered'
)
SELECT b.day_of_week, b.time_range AS existing_block,
       c.time_range AS candidate_block
FROM candidate c
JOIN busy b
  ON b.day_of_week = c.day_of_week
 AND b.time_range && c.time_range;
```

If the query returns a row, it indicates that Sarah’s existing class
(ENGR101 section A1) overlaps with the requested section (ENGR201
B1) on the same day.  The system should therefore flag a conflict
before routing the request to the advisor.  Should Sarah proceed
regardless, the request would appear in the academic advisor’s queue
with a conflict entry in the request_conflict table.

4. Resolving the request

The advisor can either reject the request due to the time conflict or
advise Sarah to select an alternative section (such as A2 on
Wednesday).  If an alternate section is chosen, the same conflict
query can be rerun, and no rows will be returned if there is no
overlap.

---

This test scenario demonstrates how the proposed schema and seed data
support the new business rules, particularly the prevention of
schedule conflicts.

## 5. Test Utterances

Here are the recommended natural language utterances to test the complete
scenario using the chat interface. Sarah Ahmed is pre-seeded with
student_id `4441ab90-e2fe-4da5-a0e1-6a129d61552f` for testing purposes.

### Step 1: Check Current Schedule
```
"What's my current schedule?"
```
**Expected result:** Should show ENGR101 A1 on Monday 10:00-11:30 and Wednesday 2:00-3:30 PM in a week grid card.

### Step 2: Browse Available Courses
```
"What courses are available this semester?"
```
**Expected result:** Should show ENGR101 and ENGR201 with their sections in a course info card. ENGR201 should show both B1 (Monday) and A2 (Tuesday) sections.

### Step 3: Look for ENGR201 Specifically
```
"Show me sections for ENGR201"
```
**Expected result:** Should show ENGR201 B1 with Monday 10:30-12:00 meeting time and ENGR201 A2 with Tuesday 9:30-11:00 meeting time.

### Step 4: Try to Add Conflicting Section
```
"I want to add ENGR201 section B1"
```
**Expected result:** Should detect time conflict, warn about overlap with existing ENGR101 A1 (Monday 10:00-11:30 vs Monday 10:30-12:00), AND proactively suggest ENGR201 A2 (Tuesday 9:30-11:00) as a non-conflicting alternative.

### Step 5: Check for Alternative Sections (Optional - now automated)
```
"Are there other sections of ENGR101 available?"
```
**Expected result:** Should show ENGR101 A2 which meets Wednesday 14:00-15:15 (no conflict). *Note: This step may be redundant now that alternatives are shown proactively in Step 4.*

### Step 6: Check Pending Requests
```
"Do I have any pending registration requests?"
```
**Expected result:** Should show any ADD requests if created during testing.

## 6. Key Features Being Tested

1. **Conflict Detection:** The `check_attachable` tool detects Monday time overlap
2. **Proactive Suggestions:** System automatically suggests alternative sections when conflicts detected
3. **Schedule Visualization:** Week grid cards showing time conflicts
4. **Course Information:** Course info cards with section details and meeting times
5. **Request Management:** Creating and tracking registration requests
6. **Alternative Discovery:** Finding non-conflicting sections automatically or on-demand
7. **Tool Integration:** SmolAgents calling appropriate tools based on natural language

The scenario validates that the chat system can understand student intent,
call the appropriate backend tools, detect scheduling conflicts, and present
information in user-friendly card formats.
