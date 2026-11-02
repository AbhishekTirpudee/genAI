# 🎓 College Result Analysis Agent

> **An Autonomous AI & SQL Analytics Engine for Academic Evaluations**  
> Answers natural language questions about student marks, overall and department-wise pass percentages, and subject-wise academic performance using an SQLite relational database.

---

## 📌 Executive Summary

The **College Result Analysis Agent** allows faculty members, department heads, and academic administrators to query complex student examination results through natural language or direct SQL.

The system translates English queries into optimized, read-only SQL queries, executes them against an SQLite database, and returns:
- **Conversational Explanations**: Contextual summaries with metrics and analysis.
- **Key Performance Indicators (KPIs)**: Instant metric chips (Pass Rate, Class Average, Top Scorers, Backlog Counts).
- **Interactive Visualizations**: Dynamic Chart.js charts (Pass vs Fail doughnuts, Subject comparison bar charts, Student radar profiles).
- **SQL Transparency**: The exact SQL executed, execution time in milliseconds (`~1-5ms`), and explanation of query logic.
- **Academic Transcripts & Marksheets**: Complete printable student report cards with SGPA and division.

---

## 🏗️ Architecture & Database Design

### Relational Schema (`college_results.db`)

The SQLite database implements a normalized relational model across 4 core tables and 4 analytical views:

```
+--------------------+        +--------------------+
|    departments     |        |      faculty       |
|--------------------|        |--------------------|
| dept_id (PK)       |        | faculty_id (PK)    |
| dept_code          |        | name, designation  |
| dept_name          |        | email, dept_id     |
+---------+----------+        +---------+----------+
          |                             |
          | 1:N                         | 1:N
          v                             v
+--------------------+        +--------------------+
|      students      |        |  subject_faculty   |
|--------------------|        +--------------------+
| student_id (PK)    |                  |
| roll_no (UNIQUE)   |                  |
| usn, name, gender  |                  |
| dept_id, sem, sec  |                  v
+---------+----------+        +--------------------+
          |                   |      subjects      |
          |                   |--------------------|
          | 1:N               | subject_id (PK)    |
          |                   | subject_code       |
          |                   | subject_name       |
          |                   | credits, max_marks |
          v                   +---------+----------+
+--------------------+                  |
|       marks        | <----------------+ 1:N
|--------------------|
| mark_id (PK)       |
| student_id (FK)    |
| subject_id (FK)    |
| internal_marks     |
| external_marks     |
| total_marks        |
| grade, grade_point |
| is_passed (0 or 1) |
+--------------------+
```

### Pre-Calculated Analytical Views:
1. **`v_student_summary`**: Aggregates total marks, percentage, SGPA (10-point scale), backlogs, and final result classification (`Distinction`, `First Class`, `Second Class`, `Pass Class`, `Fail`).
2. **`v_subject_performance`**: Aggregates for each subject: total appeared, passed, failed, pass percentage, average score, topper score, and lowest score.
3. **`v_department_performance`**: Computes department student count, pass percentage, average percentage, and average SGPA.
4. **`v_student_marks`**: Flat view joining students, departments, subjects, and marks for report card lookups.

---

## 🚀 Quick Start Guide

### 1. One-Click Launch (Windows)
Double-click `run_result_agent.bat` in the project root directory or run:
```powershell
.\run_result_agent.bat
```
This automatically opens the browser at `http://localhost:5050`.

### 2. Manual Terminal Launch
```bash
cd college_result_agent
py app.py
```
App will run on **`http://localhost:5050`**.

### 3. Run Automated Unit Tests
```bash
py college_result_agent/tests/test_agent.py
```

---

## 💬 Supported Natural Language Question Categories

| Category | Example Question | Generated SQL / Analytical View |
|---|---|---|
| **Overall Pass %** | *"What is the overall pass percentage of the college?"* | `SELECT * FROM v_student_summary` (Aggregated pass rate) |
| **Department Pass %** | *"Compare pass percentage across all departments"* | `SELECT * FROM v_department_performance ORDER BY pass_percentage DESC` |
| **Specific Dept** | *"What is the pass percentage of Computer Science?"* | `WHERE dept_code = 'CSE'` |
| **Subject Performance** | *"Show subject-wise performance for Semester 4"* | `SELECT * FROM v_subject_performance WHERE semester = 4` |
| **Toughest Subjects** | *"Which subject has the lowest pass percentage?"* | `ORDER BY pass_percentage ASC LIMIT 5` |
| **Subject Statistics** | *"What is the pass percentage in Database Management Systems?"* | `WHERE subject_code = 'CS401' OR subject_name LIKE '%Database%'` |
| **Student Marks** | *"Show complete report card for roll CS24-001"* | `SELECT * FROM v_student_marks WHERE roll_no = 'CS24-001'` |
| **Student by Name** | *"What are the marks of Priya Patel?"* | `SELECT * FROM v_student_marks WHERE UPPER(student_name) LIKE '%PRIYA PATEL%'` |
| **Top Rankers** | *"Show top 5 students in Computer Science"* | `SELECT * FROM v_student_summary WHERE dept_code = 'CSE' ORDER BY percentage DESC LIMIT 5` |
| **Subject Topper** | *"Who scored the highest marks in Operating Systems?"* | `SELECT * FROM v_student_marks WHERE subject_code = 'CS403' ORDER BY total_marks DESC LIMIT 1` |
| **Backlog List** | *"List all students who failed with backlogs"* | `SELECT * FROM v_student_summary WHERE result_status = 'Fail'` |
| **Section Analysis** | *"Compare Section A vs Section B performance"* | `GROUP BY dept_code, semester, section` |
| **Grade Distribution**| *"What is the overall grade distribution?"* | `GROUP BY result_status` |

---

## 🌐 Application Portals & Tabs

- **🤖 AI Result Agent Tab**: Interactive conversational assistant with inline Chart.js charts, SQL viewer, speech synthesis (listen to results), and one-click prompt chips.
- **📊 Analytics Dashboard Tab**: Live KPI cards (Overall Pass Rate, Total Students, Clear Passes, Backlogs, Mean SGPA), Department Comparison Bar Chart, Student Classification Doughnut Chart, and Top Rankers Leaderboard.
- **📜 Student Marksheet Tab**: Instant student dropdown to generate and print official academic transcripts with SGPA, percentage, and signature blocks.
- **📚 Subject Deep Dive Tab**: Select any subject to view enrollment, pass %, average, highest/lowest marks, and the backlog register of failing students.
- **⚡ SQL Studio Tab**: Read-only safe SQL console to run custom SQL queries with CSV export and an interactive Database Schema Explorer.
- **⚙️ AI Config**: Toggle between the built-in offline NLP engine and Google Gemini, Groq, or OpenAI.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/chat` | `POST` | Processes natural language questions into SQL + answer + chart + KPIs |
| `POST /api/sql/execute` | `POST` | Safely executes read-only SELECT queries with execution timer |
| `GET /api/dashboard/stats` | `GET` | Aggregated college KPIs, department stats, subject stats, and toppers |
| `GET /api/students` | `GET` | Filterable list of students by department, semester, and search query |
| `GET /api/student/<roll_no>`| `GET` | Full transcript and marks breakdown for a specific student |
| `GET /api/schema` | `GET` | Database schema structure and column definitions |
| `GET /api/health` | `GET` | Service health status |

---

## 🔒 Security & Safe Execution
- **Strict Read-Only Enforcement**: Blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, and chained multi-statement queries.
- **Zero External Lock-In**: Works 100% offline using standard Python standard library and Flask, with optional external LLM key support.
