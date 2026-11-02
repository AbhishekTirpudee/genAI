-- Schema for College Result Analysis System

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code TEXT UNIQUE NOT NULL,
    dept_name TEXT NOT NULL,
    hod_name TEXT
);

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT UNIQUE NOT NULL,
    usn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    email TEXT,
    dept_id INTEGER NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
    semester INTEGER NOT NULL CHECK(semester BETWEEN 1 AND 8),
    section TEXT NOT NULL CHECK(section IN ('A', 'B', 'C')),
    batch_year TEXT NOT NULL
);

-- 3. Faculty Table
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    designation TEXT,
    email TEXT,
    dept_id INTEGER REFERENCES departments(dept_id)
);

-- 4. Subjects Table
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT UNIQUE NOT NULL,
    subject_name TEXT NOT NULL,
    dept_id INTEGER NOT NULL REFERENCES departments(dept_id) ON DELETE CASCADE,
    semester INTEGER NOT NULL CHECK(semester BETWEEN 1 AND 8),
    credits INTEGER DEFAULT 3,
    max_internal INTEGER DEFAULT 30,
    max_external INTEGER DEFAULT 70,
    max_marks INTEGER DEFAULT 100,
    pass_marks INTEGER DEFAULT 40,
    is_practical INTEGER DEFAULT 0
);

-- 5. Subject Faculty Mapping Table
CREATE TABLE IF NOT EXISTS subject_faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    UNIQUE(subject_id, faculty_id)
);

-- 6. Marks Table
CREATE TABLE IF NOT EXISTS marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    exam_term TEXT DEFAULT 'End-Sem May 2024',
    internal_marks REAL CHECK(internal_marks >= 0),
    external_marks REAL CHECK(external_marks >= 0),
    total_marks REAL CHECK(total_marks >= 0 AND total_marks <= 100),
    grade TEXT NOT NULL,
    grade_point INTEGER NOT NULL,
    is_passed INTEGER NOT NULL CHECK(is_passed IN (0, 1)),
    UNIQUE(student_id, subject_id, exam_term)
);

-- 7. Analytical Views

-- View 1: Detailed Student Marks View
DROP VIEW IF EXISTS v_student_marks;
CREATE VIEW v_student_marks AS
SELECT 
    m.mark_id,
    s.student_id,
    s.roll_no,
    s.usn,
    s.name AS student_name,
    s.gender,
    d.dept_code,
    d.dept_name,
    s.semester,
    s.section,
    sub.subject_id,
    sub.subject_code,
    sub.subject_name,
    sub.credits,
    sub.pass_marks,
    m.internal_marks,
    m.external_marks,
    m.total_marks,
    m.grade,
    m.grade_point,
    m.is_passed,
    m.exam_term
FROM marks m
JOIN students s ON m.student_id = s.student_id
JOIN departments d ON s.dept_id = d.dept_id
JOIN subjects sub ON m.subject_id = sub.subject_id;

-- View 2: Student Semester Summary (SGPA, Overall Status, Total Marks, Backlogs)
DROP VIEW IF EXISTS v_student_summary;
CREATE VIEW v_student_summary AS
SELECT 
    s.student_id,
    s.roll_no,
    s.usn,
    s.name AS student_name,
    s.gender,
    d.dept_code,
    d.dept_name,
    s.semester,
    s.section,
    s.batch_year,
    COUNT(m.mark_id) AS total_subjects,
    ROUND(SUM(m.total_marks), 2) AS total_marks_obtained,
    ROUND(SUM(sub.max_marks), 2) AS total_max_marks,
    ROUND((SUM(m.total_marks) * 100.0) / SUM(sub.max_marks), 2) AS percentage,
    ROUND(SUM(m.grade_point * sub.credits) * 1.0 / SUM(sub.credits), 2) AS sgpa,
    SUM(CASE WHEN m.is_passed = 1 THEN 1 ELSE 0 END) AS subjects_passed,
    SUM(CASE WHEN m.is_passed = 0 THEN 1 ELSE 0 END) AS subjects_failed,
    CASE 
        WHEN SUM(CASE WHEN m.is_passed = 0 THEN 1 ELSE 0 END) > 0 THEN 'Fail'
        WHEN (SUM(m.total_marks) * 100.0 / SUM(sub.max_marks)) >= 75.0 THEN 'Distinction'
        WHEN (SUM(m.total_marks) * 100.0 / SUM(sub.max_marks)) >= 60.0 THEN 'First Class'
        WHEN (SUM(m.total_marks) * 100.0 / SUM(sub.max_marks)) >= 50.0 THEN 'Second Class'
        ELSE 'Pass Class'
    END AS result_status
FROM students s
JOIN departments d ON s.dept_id = d.dept_id
JOIN marks m ON s.student_id = m.student_id
JOIN subjects sub ON m.subject_id = sub.subject_id
GROUP BY s.student_id;

-- View 3: Subject Performance View
DROP VIEW IF EXISTS v_subject_performance;
CREATE VIEW v_subject_performance AS
SELECT 
    sub.subject_id,
    sub.subject_code,
    sub.subject_name,
    d.dept_code,
    d.dept_name,
    sub.semester,
    sub.credits,
    COUNT(m.mark_id) AS total_appeared,
    SUM(CASE WHEN m.is_passed = 1 THEN 1 ELSE 0 END) AS passed_count,
    SUM(CASE WHEN m.is_passed = 0 THEN 1 ELSE 0 END) AS failed_count,
    ROUND(SUM(CASE WHEN m.is_passed = 1 THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(m.mark_id), 2) AS pass_percentage,
    ROUND(AVG(m.total_marks), 2) AS average_marks,
    ROUND(MAX(m.total_marks), 2) AS highest_marks,
    ROUND(MIN(m.total_marks), 2) AS lowest_marks
FROM subjects sub
JOIN departments d ON sub.dept_id = d.dept_id
LEFT JOIN marks m ON sub.subject_id = m.subject_id
GROUP BY sub.subject_id;

-- View 4: Department Performance View
DROP VIEW IF EXISTS v_department_performance;
CREATE VIEW v_department_performance AS
SELECT 
    d.dept_id,
    d.dept_code,
    d.dept_name,
    COUNT(DISTINCT summ.student_id) AS total_students,
    SUM(CASE WHEN summ.result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
    SUM(CASE WHEN summ.result_status = 'Fail' THEN 1 ELSE 0 END) AS failed_students,
    ROUND(SUM(CASE WHEN summ.result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(DISTINCT summ.student_id), 2) AS pass_percentage,
    ROUND(AVG(summ.percentage), 2) AS average_percentage,
    ROUND(AVG(summ.sgpa), 2) AS average_sgpa
FROM departments d
JOIN v_student_summary summ ON d.dept_code = summ.dept_code
GROUP BY d.dept_id;

-- Indexes for lightning fast queries
CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_no);
CREATE INDEX IF NOT EXISTS idx_students_dept ON students(dept_id);
CREATE INDEX IF NOT EXISTS idx_students_sem ON students(semester);
CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(subject_code);
CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id);
CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject_id);
CREATE INDEX IF NOT EXISTS idx_marks_passed ON marks(is_passed);
