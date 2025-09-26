Test scenario: detecting a schedule conflict

This document outlines a simple end‑to‑end scenario that demonstrates
how the extended schema can be used to detect a time conflict when a
student attempts to register for an overlapping section.  It assumes
you have executed the DDL contained in create_tables.sql and
populated the tables using the records from seed_personas.py.

1. Seed the database
	1.	Run create_tables.sql to create all tables.
	2.	Use the data returned by get_seed_data() in seed_personas.py to
insert records into the tables.  For example, in Python with
psycopg2 you could iterate over each table name and execute bulk
INSERT statements.

After seeding, the following notable rows should exist:
	•	Students – Sarah Ahmed (external_sis_id = 'S1001') is a
second‑year engineering student with no financial hold.
	•	Courses – ENGR101 (course A) and ENGR201 (course B), both
major courses offered at the main campus.
	•	Sections – three sections are available:
	•	A1 and A2 for ENGR101
	•	B1 for ENGR201
	•	Meetings – A1 meets on Monday 10:00–11:15 and B1 meets on
Monday 10:30–11:45.
	•	Enrollment – Sarah is already registered in section A1.

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

⸻

This test scenario demonstrates how the proposed schema and seed data
support the new business rules, particularly the prevention of
schedule conflicts.
