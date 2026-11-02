"""
College Result Analysis Agent - Core Query Engine.
Processes natural language queries into safe SQL, executes them against SQLite,
and produces human-like explanations, KPI metrics, and chart configurations.
"""

import re
from database.db import execute_safe_query, get_schema_summary
from agent.safety import sanitize_and_validate_sql
from agent.llm_connector import LLMConnector

class ResultAnalysisAgent:
    def __init__(self, api_key=None, provider=None):
        self.llm = LLMConnector(api_key=api_key, provider=provider)
        self.schema = get_schema_summary()

    def process_query(self, user_question: str) -> dict:
        """
        Main entrypoint. Takes a natural language question and returns:
        - conversational answer
        - executed SQL
        - execution time
        - columns & rows (tabular data)
        - kpis (key metrics)
        - chart_config (for Chart.js)
        - query_explanation
        """
        user_question = user_question.strip()
        if not user_question:
            return {
                "answer": "Please ask a question about student marks, pass percentage, or subject-wise performance.",
                "sql": None,
                "data": [],
                "columns": [],
                "kpis": {},
                "chart": None,
                "explanation": "No question entered."
            }

        # 1. Try Pattern-Based Semantic Intent Recognition (Instant & 100% Reliable Offline)
        intent_result = self._match_known_intent(user_question)
        if intent_result:
            return self._execute_and_format(intent_result, user_question)

        # 2. If LLM is configured, try LLM Text-to-SQL
        if self.llm.is_available():
            try:
                llm_result = self._query_with_llm(user_question)
                if llm_result:
                    return self._execute_and_format(llm_result, user_question)
            except Exception as e:
                # Fallback to general semantic parser if LLM fails
                pass

        # 3. Fallback to Flexible Semantic Fallback Engine
        fallback_result = self._fallback_semantic_engine(user_question)
        return self._execute_and_format(fallback_result, user_question)

    def _execute_and_format(self, intent_spec: dict, user_question: str) -> dict:
        sql = intent_spec.get("sql", "").strip()
        explanation = intent_spec.get("explanation", "")
        params = intent_spec.get("params", ())

        is_valid, clean_sql, error_msg = sanitize_and_validate_sql(sql)
        if not is_valid:
            return {
                "answer": f"I couldn't process this query securely: {error_msg}",
                "sql": sql,
                "data": [],
                "columns": [],
                "kpis": {},
                "chart": None,
                "explanation": error_msg,
                "success": False
            }

        query_res = execute_safe_query(clean_sql, params)
        if not query_res['success']:
            return {
                "answer": f"Database query error: {query_res['error']}",
                "sql": clean_sql,
                "data": [],
                "columns": [],
                "kpis": {},
                "chart": None,
                "explanation": "Execution failed in SQLite engine.",
                "success": False
            }

        rows = query_res['rows']
        cols = query_res['columns']

        # Format natural conversational answer, KPI metrics, and chart
        formatter = intent_spec.get("formatter")
        if formatter and callable(formatter):
            formatted_data = formatter(rows, user_question)
        else:
            formatted_data = self._default_formatter(rows, user_question, intent_spec.get("intent_type"))

        return {
            "answer": formatted_data.get("answer", "Here are the query results:"),
            "sql": clean_sql,
            "data": rows,
            "columns": cols,
            "row_count": len(rows),
            "execution_time_ms": query_res['execution_time_ms'],
            "kpis": formatted_data.get("kpis", {}),
            "chart": formatted_data.get("chart", None),
            "explanation": explanation or "Executed analytical SQL query against the college results database.",
            "intent_type": intent_spec.get("intent_type", "general"),
            "success": True
        }

    # -------------------------------------------------------------
    # 1. Pattern-Based Semantic Intent Recognition
    # -------------------------------------------------------------
    def _match_known_intent(self, q: str) -> dict | None:
        q_lower = q.lower()

        # Reserve words that should never be mistaken for student names
        RESERVED_WORDS = {
            'computer science', 'information technology', 'operating systems', 
            'database management', 'discrete mathematics', 'section a', 'section b',
            'semester 1', 'semester 2', 'semester 3', 'semester 4', 'semester 5',
            'all subjects', 'each subject', 'top students', 'rank list', 'digital electronics',
            'web technologies', 'cyber security', 'cloud computing', 'fluid mechanics',
            'signals and', 'microprocessors'
        }

        # 1. TOUGHEST / LOWEST PASS PERCENTAGE SUBJECTS (Check before generic subject pass %)
        if any(w in q_lower for w in ['lowest pass percentage', 'hardest subject', 'toughest subject', 'lowest pass rate', 'most difficult subject', 'least pass percentage']):
            return {
                "intent_type": "toughest_subjects",
                "sql": """
                    SELECT 
                        subject_code, subject_name, dept_code, semester,
                        total_appeared, passed_count, failed_count, pass_percentage,
                        average_marks, highest_marks, lowest_marks
                    FROM v_subject_performance
                    ORDER BY pass_percentage ASC
                    LIMIT 5
                """,
                "explanation": "Identifies the subjects with the lowest pass percentages across the college.",
                "formatter": self._format_toughest_easiest_subjects
            }

        # 2. EASIEST / HIGHEST PASS PERCENTAGE SUBJECTS
        if any(w in q_lower for w in ['highest pass percentage', 'easiest subject', 'highest pass rate', 'best subject', 'top pass percentage']):
            return {
                "intent_type": "easiest_subjects",
                "sql": """
                    SELECT 
                        subject_code, subject_name, dept_code, semester,
                        total_appeared, passed_count, failed_count, pass_percentage,
                        average_marks, highest_marks, lowest_marks
                    FROM v_subject_performance
                    ORDER BY pass_percentage DESC
                    LIMIT 5
                """,
                "explanation": "Identifies the subjects with the highest pass percentages across the college.",
                "formatter": self._format_toughest_easiest_subjects
            }

        # 3. SECTION COMPARISON (Section A vs Section B)
        if any(w in q_lower for w in ['section a', 'section b', 'compare sections', 'section wise', 'section-wise', 'sections']):
            return {
                "intent_type": "section_comparison",
                "sql": """
                    SELECT 
                        dept_code, semester, section,
                        COUNT(*) AS total_students,
                        SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                        ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                        ROUND(AVG(percentage), 2) AS average_percentage,
                        ROUND(AVG(sgpa), 2) AS average_sgpa
                    FROM v_student_summary
                    GROUP BY dept_code, semester, section
                    ORDER BY dept_code, semester, section
                """,
                "explanation": "Compares performance metrics (Pass %, Average Score, Average SGPA) between class sections.",
                "formatter": self._format_section_comparison
            }

        # 4. SUBJECT TOPPER (Who scored highest in a subject)
        if any(w in q_lower for w in ['highest in', 'topped in', 'topper of', 'highest marks in', 'maximum marks in', 'scorer in', 'scored the highest']):
            subj = self._extract_subject(q)
            if subj:
                return {
                    "intent_type": "subject_topper",
                    "sql": """
                        SELECT 
                            roll_no, student_name, dept_code, semester, section,
                            subject_code, subject_name, internal_marks, external_marks, total_marks, grade
                        FROM v_student_marks
                        WHERE UPPER(subject_code) LIKE ? OR UPPER(subject_name) LIKE ?
                        ORDER BY total_marks DESC
                        LIMIT 5
                    """,
                    "params": (f"%{subj.upper()}%", f"%{subj.upper()}%"),
                    "explanation": f"Retrieves the highest scoring students in subject matching '{subj}'.",
                    "formatter": self._format_subject_topper
                }

        # 5. TOP PERFORMERS / TOPPERS / RANK LIST
        if any(w in q_lower for w in ['topper', 'highest marks', 'top students', 'top 5', 'top 10', 'top 3', 'rank list', 'rankers', 'highest scorer', 'best students']):
            limit = 5
            limit_match = re.search(r'top\s*(\d+)', q_lower)
            if limit_match:
                limit = int(limit_match.group(1))

            dept_filter = self._extract_department(q_lower)
            sem_filter = self._extract_semester(q_lower)

            conditions = ["result_status != 'Fail'"]
            params = []

            if dept_filter:
                conditions.append("UPPER(dept_code) = UPPER(?)")
                params.append(dept_filter)
            if sem_filter:
                conditions.append("semester = ?")
                params.append(sem_filter)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            return {
                "intent_type": "toppers",
                "sql": f"""
                    SELECT 
                        roll_no, student_name, dept_code, semester, section,
                        total_marks_obtained, total_max_marks, percentage, sgpa, result_status
                    FROM v_student_summary
                    {where_clause}
                    ORDER BY percentage DESC, sgpa DESC
                    LIMIT {limit}
                """,
                "params": tuple(params),
                "explanation": f"Retrieves the top {limit} academic performers ranked by overall percentage and SGPA.",
                "formatter": self._format_toppers
            }

        # A. SINGLE STUDENT LOOKUP (Roll number or Student Name)
        roll_match = re.search(r'\b([A-Za-z]{2,4}[-\s]?\d{2}[-\s]?\d{2,4}|1RS\w+)\b', q, re.IGNORECASE)
        if roll_match and any(w in q_lower for w in ['marks', 'result', 'card', 'report', 'score', 'performance', 'details', 'show', 'student', 'roll', 'profile']):
            raw_roll = roll_match.group(1).upper().replace(" ", "-")
            if not "-" in raw_roll and len(raw_roll) >= 6 and not raw_roll.startswith('1RS'):
                raw_roll = f"{raw_roll[:4]}-{raw_roll[4:]}"
            return {
                "intent_type": "student_report_card",
                "sql": """
                    SELECT 
                        roll_no, student_name, dept_code, semester, section,
                        subject_code, subject_name, credits, internal_marks, external_marks,
                        total_marks, grade, grade_point, is_passed
                    FROM v_student_marks 
                    WHERE UPPER(roll_no) LIKE ? OR UPPER(usn) LIKE ?
                    ORDER BY subject_code
                """,
                "params": (f"%{raw_roll}%", f"%{raw_roll}%"),
                "explanation": f"Fetched complete subject-wise marks breakdown and performance records for student with Roll No / USN matching '{raw_roll}'.",
                "formatter": self._format_student_report
            }

        # Check for student name lookup
        student_name_match = re.search(r'(?:marks|result|report card|score|performance) (?:of|for) ([A-Za-z]+ [A-Za-z]+)', q, re.IGNORECASE)
        if not student_name_match:
            student_name_match = re.search(r'([A-Za-z]+ [A-Za-z]+)(?:\'s|s)? (?:marks|result|report card|score|performance)', q, re.IGNORECASE)
        if student_name_match:
            candidate_name = student_name_match.group(1).strip()
            if candidate_name.lower() not in RESERVED_WORDS and not any(r in candidate_name.lower() for r in ['section', 'semester', 'department']):
                return {
                    "intent_type": "student_report_card",
                    "sql": """
                        SELECT 
                            roll_no, student_name, dept_code, semester, section,
                            subject_code, subject_name, credits, internal_marks, external_marks,
                            total_marks, grade, grade_point, is_passed
                        FROM v_student_marks 
                        WHERE UPPER(student_name) LIKE ?
                        ORDER BY subject_code
                    """,
                    "params": (f"%{candidate_name.upper()}%",),
                    "explanation": f"Filtered student marks records by matching name '{candidate_name}'.",
                    "formatter": self._format_student_report
                }

        # B. OVERALL COLLEGE PASS PERCENTAGE
        if any(p in q_lower for p in [
            'overall pass percentage', 'college pass percentage', 'total pass percentage', 
            'overall result', 'overall pass rate', 'what is the pass percentage of the college',
            'overall pass %', 'pass percentage overall'
        ]):
            return {
                "intent_type": "overall_pass_percentage",
                "sql": """
                    SELECT 
                        COUNT(*) AS total_students,
                        SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                        SUM(CASE WHEN result_status = 'Fail' THEN 1 ELSE 0 END) AS failed_students,
                        ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                        ROUND(AVG(percentage), 2) AS college_average_percentage,
                        ROUND(AVG(sgpa), 2) AS college_average_sgpa
                    FROM v_student_summary
                """,
                "explanation": "Calculates the total student count, number of passed and failed students, and the overall college pass percentage based on student summary standings.",
                "formatter": self._format_overall_pass_percentage
            }

        # C. DEPARTMENT-WISE PASS PERCENTAGE / COMPARISON
        if ('department' in q_lower or 'dept' in q_lower or any(d in q_lower for d in ['cse', 'it', 'ece', 'mech', 'computer science', 'information tech'])) and \
           any(w in q_lower for w in ['pass percentage', 'pass rate', 'passed', 'performance', 'compare', 'pass %']):
            
            # Check if specific department requested
            dept_code = self._extract_department(q_lower)
            if dept_code and not any(w in q_lower for w in ['compare', 'all departments', 'each department', 'department wise', 'department-wise']):
                return {
                    "intent_type": "dept_pass_percentage",
                    "sql": """
                        SELECT 
                            dept_code, dept_name, total_students, passed_students, failed_students,
                            pass_percentage, average_percentage, average_sgpa
                        FROM v_department_performance
                        WHERE UPPER(dept_code) = UPPER(?)
                    """,
                    "params": (dept_code,),
                    "explanation": f"Retrieves student count, pass percentage, and academic metrics specifically for the {dept_code} department.",
                    "formatter": self._format_department_performance
                }
            else:
                return {
                    "intent_type": "dept_comparison",
                    "sql": """
                        SELECT 
                            dept_code, dept_name, total_students, passed_students, failed_students,
                            pass_percentage, average_percentage, average_sgpa
                        FROM v_department_performance
                        ORDER BY pass_percentage DESC
                    """,
                    "explanation": "Aggregates and compares pass percentage, student count, and average percentage across all academic departments.",
                    "formatter": self._format_department_performance
                }

        # D. SUBJECT-WISE PASS PERCENTAGE & PERFORMANCE
        if any(w in q_lower for w in ['subject-wise', 'subject wise', 'all subjects', 'subject performance', 'performance of subjects']) or \
           ('pass percentage' in q_lower and 'subject' in q_lower):
            
            sem_filter = self._extract_semester(q_lower)
            if sem_filter:
                return {
                    "intent_type": "subject_performance_all",
                    "sql": """
                        SELECT 
                            subject_code, subject_name, dept_code, semester, credits,
                            total_appeared, passed_count, failed_count, pass_percentage,
                            average_marks, highest_marks, lowest_marks
                        FROM v_subject_performance
                        WHERE semester = ?
                        ORDER BY pass_percentage DESC
                    """,
                    "params": (sem_filter,),
                    "explanation": f"Calculates subject-wise pass percentage, student count, average, highest, and lowest marks for Semester {sem_filter}.",
                    "formatter": self._format_subject_performance
                }
            else:
                return {
                    "intent_type": "subject_performance_all",
                    "sql": """
                        SELECT 
                            subject_code, subject_name, dept_code, semester, credits,
                            total_appeared, passed_count, failed_count, pass_percentage,
                            average_marks, highest_marks, lowest_marks
                        FROM v_subject_performance
                        ORDER BY pass_percentage DESC
                    """,
                    "explanation": "Calculates subject-wise pass percentage, student count, average, highest, and lowest marks across all subjects.",
                    "formatter": self._format_subject_performance
                }

        # E. SPECIFIC SUBJECT PERFORMANCE / PASS PERCENTAGE
        # E.g. "pass percentage in DBMS", "performance in Algorithms", "average marks in Operating Systems"
        subject_candidate = self._extract_subject(q)
        if subject_candidate and any(w in q_lower for w in ['pass percentage', 'performance', 'average', 'marks', 'stats', 'result', 'pass %', 'highest', 'lowest']):
            return {
                "intent_type": "single_subject_performance",
                "sql": """
                    SELECT 
                        subject_code, subject_name, dept_code, semester, credits,
                        total_appeared, passed_count, failed_count, pass_percentage,
                        average_marks, highest_marks, lowest_marks
                    FROM v_subject_performance
                    WHERE UPPER(subject_code) LIKE ? OR UPPER(subject_name) LIKE ?
                """,
                "params": (f"%{subject_candidate.upper()}%", f"%{subject_candidate.upper()}%"),
                "explanation": f"Retrieves statistical summary (pass percentage, average marks, topper marks) for subject matching '{subject_candidate}'.",
                "formatter": self._format_single_subject
            }

        # J. FAILED STUDENTS / BACKLOGS / ARREARS
        if any(w in q_lower for w in ['failed', 'backlog', 'backlogs', 'arrear', 'arrears', 'fail list', 'failing']):
            subj = self._extract_subject(q)
            if subj:
                # Failed in specific subject
                return {
                    "intent_type": "subject_failures",
                    "sql": """
                        SELECT 
                            roll_no, student_name, dept_code, semester, section,
                            subject_code, subject_name, internal_marks, external_marks, total_marks, grade
                        FROM v_student_marks
                        WHERE is_passed = 0 AND (UPPER(subject_code) LIKE ? OR UPPER(subject_name) LIKE ?)
                        ORDER BY total_marks ASC
                    """,
                    "params": (f"%{subj.upper()}%", f"%{subj.upper()}%"),
                    "explanation": f"Retrieves list of students who did not pass subject matching '{subj}'.",
                    "formatter": self._format_failed_students
                }
            else:
                # General failures or students with backlogs
                dept_filter = self._extract_department(q_lower)
                sem_filter = self._extract_semester(q_lower)
                conditions = ["result_status = 'Fail'"]
                params = []
                if dept_filter:
                    conditions.append("UPPER(dept_code) = UPPER(?)")
                    params.append(dept_filter)
                if sem_filter:
                    conditions.append("semester = ?")
                    params.append(sem_filter)

                return {
                    "intent_type": "student_backlogs",
                    "sql": f"""
                        SELECT 
                            roll_no, student_name, dept_code, semester, section,
                            total_marks_obtained, percentage, subjects_failed, result_status
                        FROM v_student_summary
                        WHERE {' AND '.join(conditions)}
                        ORDER BY subjects_failed DESC, percentage ASC
                    """,
                    "params": tuple(params),
                    "explanation": "Lists students with active backlogs along with the number of subjects failed.",
                    "formatter": self._format_failed_students
                }

        # K. GRADE DISTRIBUTION / CLASSIFICATION (Distinction, First Class, etc.)
        if any(w in q_lower for w in ['grade distribution', 'grades', 'distinction', 'first class', 'second class', 'division']):
            dept_filter = self._extract_department(q_lower)
            where = f"WHERE UPPER(dept_code) = UPPER('{dept_filter}')" if dept_filter else ""
            return {
                "intent_type": "grade_distribution",
                "sql": f"""
                    SELECT 
                        result_status,
                        COUNT(*) AS student_count,
                        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM v_student_summary {where}), 2) AS percentage_of_total
                    FROM v_student_summary
                    {where}
                    GROUP BY result_status
                    ORDER BY 
                        CASE result_status 
                            WHEN 'Distinction' THEN 1
                            WHEN 'First Class' THEN 2
                            WHEN 'Second Class' THEN 3
                            WHEN 'Pass Class' THEN 4
                            ELSE 5
                        END
                """,
                "explanation": "Calculates overall distribution of student outcomes: Distinction, First Class, Second Class, and Fail.",
                "formatter": self._format_grade_distribution
            }

        # L. SECTION COMPARISON (Section A vs Section B)
        if any(w in q_lower for w in ['section a', 'section b', 'compare sections', 'section wise', 'section-wise']):
            return {
                "intent_type": "section_comparison",
                "sql": """
                    SELECT 
                        dept_code, semester, section,
                        COUNT(*) AS total_students,
                        SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                        ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                        ROUND(AVG(percentage), 2) AS average_percentage,
                        ROUND(AVG(sgpa), 2) AS average_sgpa
                    FROM v_student_summary
                    GROUP BY dept_code, semester, section
                    ORDER BY dept_code, semester, section
                """,
                "explanation": "Compares performance metrics (Pass %, Average Score, Average SGPA) between class sections.",
                "formatter": self._format_section_comparison
            }

        # M. SEMESTER COMPARISON
        if any(w in q_lower for w in ['semester wise', 'semester-wise', 'compare semesters', 'all semesters']):
            return {
                "intent_type": "semester_comparison",
                "sql": """
                    SELECT 
                        semester,
                        COUNT(*) AS total_students,
                        SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                        ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                        ROUND(AVG(percentage), 2) AS average_percentage,
                        ROUND(AVG(sgpa), 2) AS average_sgpa
                    FROM v_student_summary
                    GROUP BY semester
                    ORDER BY semester
                """,
                "explanation": "Calculates academic performance and pass percentage grouped by semester.",
                "formatter": self._format_semester_comparison
            }

        return None

    # -------------------------------------------------------------
    # 2. General Fallback Semantic Engine
    # -------------------------------------------------------------
    def _fallback_semantic_engine(self, q: str) -> dict:
        q_lower = q.lower()
        dept = self._extract_department(q_lower)
        sem = self._extract_semester(q_lower)

        # If asking about pass percentage or rate
        if 'pass' in q_lower or 'percentage' in q_lower or 'rate' in q_lower:
            conditions = []
            params = []
            if dept:
                conditions.append("dept_code = ?")
                params.append(dept)
            if sem:
                conditions.append("semester = ?")
                params.append(sem)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            return {
                "intent_type": "dynamic_pass_summary",
                "sql": f"""
                    SELECT 
                        COUNT(*) AS total_students,
                        SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                        SUM(CASE WHEN result_status = 'Fail' THEN 1 ELSE 0 END) AS failed_students,
                        ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                        ROUND(AVG(percentage), 2) AS average_percentage,
                        ROUND(AVG(sgpa), 2) AS average_sgpa
                    FROM v_student_summary
                    {where}
                """,
                "params": tuple(params),
                "explanation": "Calculated pass percentage and aggregate performance for matching student cohort.",
                "formatter": self._format_overall_pass_percentage
            }

        # If asking about students or marks
        if any(w in q_lower for w in ['student', 'marks', 'score', 'average', 'list', 'show']):
            conditions = []
            params = []
            if dept:
                conditions.append("dept_code = ?")
                params.append(dept)
            if sem:
                conditions.append("semester = ?")
                params.append(sem)
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            return {
                "intent_type": "students_overview",
                "sql": f"""
                    SELECT 
                        roll_no, student_name, dept_code, semester, section,
                        total_marks_obtained, percentage, sgpa, result_status
                    FROM v_student_summary
                    {where}
                    ORDER BY percentage DESC
                    LIMIT 20
                """,
                "params": tuple(params),
                "explanation": "Retrieved student marks summary matching query criteria.",
                "formatter": self._format_toppers
            }

        # Default fallback to department performance overview
        return {
            "intent_type": "general_overview",
            "sql": "SELECT dept_code, dept_name, total_students, passed_students, pass_percentage, average_percentage FROM v_department_performance",
            "explanation": "Displayed general department-level academic performance metrics.",
            "formatter": self._format_department_performance
        }

    # -------------------------------------------------------------
    # 3. LLM-Based Query Generator (Optional)
    # -------------------------------------------------------------
    def _query_with_llm(self, question: str) -> dict | None:
        system_prompt = f"""
You are an expert SQL Generator for a College Result Analysis Database.
The SQLite database has these key views and tables:
1. v_student_summary (student_id, roll_no, usn, student_name, gender, dept_code, dept_name, semester, section, batch_year, total_subjects, total_marks_obtained, total_max_marks, percentage, sgpa, subjects_passed, subjects_failed, result_status ['Distinction','First Class','Second Class','Pass Class','Fail'])
2. v_subject_performance (subject_id, subject_code, subject_name, dept_code, dept_name, semester, credits, total_appeared, passed_count, failed_count, pass_percentage, average_marks, highest_marks, lowest_marks)
3. v_department_performance (dept_id, dept_code, dept_name, total_students, passed_students, failed_students, pass_percentage, average_percentage, average_sgpa)
4. v_student_marks (mark_id, student_id, roll_no, usn, student_name, gender, dept_code, dept_name, semester, section, subject_id, subject_code, subject_name, credits, pass_marks, internal_marks, external_marks, total_marks, grade, grade_point, is_passed, exam_term)

RULES:
- Return ONLY valid SQLite read-only SELECT queries.
- Do NOT use markdown code blocks or formatting. Output only the pure raw SQL string.
- Prefer querying the views (v_student_summary, v_subject_performance, v_department_performance, v_student_marks) for performance.
"""
        response_text = self.llm.query_llm(question, system_prompt).strip()
        cleaned = re.sub(r'^```(?:sql)?\s*|\s*```$', '', response_text, flags=re.MULTILINE).strip()
        
        if cleaned.upper().startswith("SELECT") or cleaned.upper().startswith("WITH"):
            return {
                "intent_type": "llm_generated",
                "sql": cleaned,
                "explanation": "Generated custom SQL query using AI LLM model based on your query.",
                "formatter": None
            }
        return None

    # -------------------------------------------------------------
    # 4. Helper Entity Extractors
    # -------------------------------------------------------------
    def _extract_department(self, q: str) -> str | None:
        mapping = {
            'computer science': 'CSE',
            'cs ': 'CSE',
            'cse': 'CSE',
            'information tech': 'IT',
            'it ': 'IT',
            'electronics': 'ECE',
            'entc': 'ECE',
            'ece': 'ECE',
            'mechanical': 'MECH',
            'mech': 'MECH'
        }
        for k, v in mapping.items():
            if k in q:
                return v
        return None

    def _extract_semester(self, q: str) -> int | None:
        sem_match = re.search(r'(?:sem(?:ester)?|term)\s*([1-8])\b', q)
        if sem_match:
            return int(sem_match.group(1))
        num_match = re.search(r'\b([1-8])(?:st|nd|rd|th)?\s*sem(?:ester)?\b', q)
        if num_match:
            return int(num_match.group(1))
        return None

    def _extract_subject(self, q: str) -> str | None:
        # Check by known code
        codes = ['CS401', 'CS402', 'CS403', 'CS404', 'CS405', 'CS301', 'CS302', 'CS303',
                 'IT401', 'IT402', 'IT403', 'IT404', 'EC401', 'EC402', 'EC403', 'ME401', 'ME402', 'ME403']
        for c in codes:
            if c.lower() in q.lower():
                return c

        # Check by keywords
        keywords = [
            ('database', 'Database'),
            ('dbms', 'Database Management'),
            ('algorithm', 'Algorithms'),
            ('operating system', 'Operating Systems'),
            ('os', 'Operating Systems'),
            ('computer network', 'Computer Networks'),
            ('network', 'Computer Networks'),
            ('cn', 'Computer Networks'),
            ('software engineering', 'Software Engineering'),
            ('data structure', 'Data Structures'),
            ('dsa', 'Data Structures'),
            ('discrete math', 'Discrete Mathematics'),
            ('digital electronic', 'Digital Electronics'),
            ('web tech', 'Web Technologies'),
            ('cyber security', 'Information & Cyber Security'),
            ('security', 'Information & Cyber Security'),
            ('cloud', 'Cloud Computing'),
            ('signal', 'Signals and Digital'),
            ('microprocessor', 'Microprocessors'),
            ('thermodynamics', 'Thermodynamics'),
            ('fluid', 'Fluid Mechanics'),
            ('manufacturing', 'Manufacturing Processes')
        ]
        q_clean = q.lower()
        for k, v in keywords:
            if len(k) <= 2:
                if re.search(rf'\b{k}\b', q_clean):
                    return v
            else:
                if k in q_clean:
                    return v
        return None

    # -------------------------------------------------------------
    # 5. Domain-Specific Formatters & Visualizers
    # -------------------------------------------------------------
    def _format_overall_pass_percentage(self, rows, q):
        if not rows:
            return {"answer": "No result data available to calculate overall pass percentage."}
        r = rows[0]
        pass_pct = r.get('pass_percentage', 0)
        tot = r.get('total_students', 0)
        passed = r.get('passed_students', 0)
        failed = r.get('failed_students', 0)
        avg_pct = r.get('college_average_percentage', 0)
        avg_sgpa = r.get('college_average_sgpa', 0)

        answer = (
            f"🎓 **Overall College Pass Percentage: {pass_pct}%**\n\n"
            f"- **Total Students Evaluated:** {tot}\n"
            f"- **Passed (All Clear):** {passed} students ({(passed*100.0/tot):.1f}%)\n"
            f"- **Failed / Backlogs:** {failed} students ({(failed*100.0/tot):.1f}%)\n"
            f"- **College Mean Percentage:** {avg_pct}%\n"
            f"- **College Mean SGPA:** {avg_sgpa} / 10.0"
        )

        chart = {
            "type": "doughnut",
            "title": "College Pass vs Fail Distribution",
            "labels": ["Passed (All Clear)", "Failed / With Backlogs"],
            "datasets": [{
                "data": [passed, failed],
                "backgroundColor": ["#10B981", "#EF4444"],
                "borderColor": ["#059669", "#DC2626"]
            }]
        }

        kpis = {
            "Overall Pass Rate": f"{pass_pct}%",
            "Total Students": tot,
            "Clear Passes": passed,
            "Backlogs": failed,
            "Avg SGPA": avg_sgpa
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_department_performance(self, rows, q):
        if not rows:
            return {"answer": "No department performance records found."}

        labels = [r.get('dept_code') for r in rows]
        pass_rates = [r.get('pass_percentage') for r in rows]
        avg_scores = [r.get('average_percentage') for r in rows]

        # Top dept
        top_dept = max(rows, key=lambda x: x.get('pass_percentage', 0))
        
        answer = f"📊 **Department Performance Overview**\n\n"
        answer += f"The **{top_dept.get('dept_name')} ({top_dept.get('dept_code')})** department achieved the highest pass percentage at **{top_dept.get('pass_percentage')}%**.\n\n"
        answer += "| Department | Total Students | Passed | Pass % | Avg Score % | Avg SGPA |\n"
        answer += "|---|---|---|---|---|---|\n"
        for r in rows:
            answer += f"| **{r.get('dept_code')}** | {r.get('total_students')} | {r.get('passed_students')} | **{r.get('pass_percentage')}%** | {r.get('average_percentage')}% | {r.get('average_sgpa')} |\n"

        chart = {
            "type": "bar",
            "title": "Pass Percentage by Department",
            "labels": labels,
            "datasets": [
                {
                    "label": "Pass Percentage (%)",
                    "data": pass_rates,
                    "backgroundColor": "#3B82F6"
                },
                {
                    "label": "Average Score (%)",
                    "data": avg_scores,
                    "backgroundColor": "#8B5CF6"
                }
            ]
        }

        kpis = {
            "Top Department": f"{top_dept.get('dept_code')} ({top_dept.get('pass_percentage')}%)",
            "Departments": len(rows),
            "Highest Avg": f"{max(avg_scores)}%"
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_subject_performance(self, rows, q):
        if not rows:
            return {"answer": "No subject performance records found."}

        labels = [r.get('subject_name')[:22] + "..." if len(r.get('subject_name', '')) > 22 else r.get('subject_name') for r in rows]
        pass_rates = [r.get('pass_percentage') for r in rows]
        avg_marks = [r.get('average_marks') for r in rows]

        highest_subj = max(rows, key=lambda x: x.get('pass_percentage', 0))
        lowest_subj = min(rows, key=lambda x: x.get('pass_percentage', 0))

        answer = (
            f"📚 **Subject-Wise Performance Analysis ({len(rows)} Subjects)**\n\n"
            f"- 🌟 **Highest Pass Rate:** {highest_subj.get('subject_name')} ({highest_subj.get('pass_percentage')}%)\n"
            f"- ⚠️ **Lowest Pass Rate (Toughest):** {lowest_subj.get('subject_name')} ({lowest_subj.get('pass_percentage')}%)\n\n"
            f"See the detailed breakdown table below for enrolled counts, failure tallies, and high/low scores."
        )

        chart = {
            "type": "bar",
            "title": "Subject Pass Rate (%) and Average Marks",
            "labels": labels,
            "datasets": [
                {
                    "label": "Pass Percentage (%)",
                    "data": pass_rates,
                    "backgroundColor": "#10B981"
                },
                {
                    "label": "Average Marks",
                    "data": avg_marks,
                    "backgroundColor": "#6366F1"
                }
            ]
        }

        kpis = {
            "Total Subjects": len(rows),
            "Easiest Subject": f"{highest_subj.get('subject_code')} ({highest_subj.get('pass_percentage')}%)",
            "Toughest Subject": f"{lowest_subj.get('subject_code')} ({lowest_subj.get('pass_percentage')}%)"
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_single_subject(self, rows, q):
        if not rows:
            return {"answer": "No subject found matching that description."}
        r = rows[0]
        name = r.get('subject_name')
        code = r.get('subject_code')
        pass_pct = r.get('pass_percentage')
        tot = r.get('total_appeared')
        passed = r.get('passed_count')
        failed = r.get('failed_count')
        avg = r.get('average_marks')
        high = r.get('highest_marks')
        low = r.get('lowest_marks')

        answer = (
            f"📖 **Subject Performance Report: {name} ({code})**\n\n"
            f"- **Department:** {r.get('dept_code')} | **Semester:** {r.get('semester')} | **Credits:** {r.get('credits')}\n"
            f"- **Pass Percentage:** **{pass_pct}%**\n"
            f"- **Students Appeared:** {tot} | **Passed:** {passed} | **Failed:** {failed}\n"
            f"- **Average Marks:** {avg} / 100\n"
            f"- **Highest Mark Scored:** {high} / 100\n"
            f"- **Lowest Mark Scored:** {low} / 100"
        )

        chart = {
            "type": "doughnut",
            "title": f"{code} Result Breakdown",
            "labels": ["Passed", "Failed"],
            "datasets": [{
                "data": [passed, failed],
                "backgroundColor": ["#10B981", "#EF4444"]
            }]
        }

        kpis = {
            "Subject": code,
            "Pass Rate": f"{pass_pct}%",
            "Class Average": f"{avg}/100",
            "Topper Score": f"{high}",
            "Backlogs": failed
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_toughest_easiest_subjects(self, rows, q):
        if not rows:
            return {"answer": "No subject statistics available."}
        
        is_toughest = "lowest" in q.lower() or "hardest" in q.lower() or "toughest" in q.lower()
        title = "Challenging (Lowest Pass %)" if is_toughest else "Highest Pass %"

        answer = f"🎯 **Top {len(rows)} {title} Subjects**\n\n"
        for idx, r in enumerate(rows, 1):
            answer += f"{idx}. **{r.get('subject_name')} ({r.get('subject_code')})** — **{r.get('pass_percentage')}% pass rate** (Avg: {r.get('average_marks')}, Failed: {r.get('failed_count')})\n"

        labels = [r.get('subject_code') for r in rows]
        pass_rates = [r.get('pass_percentage') for r in rows]

        chart = {
            "type": "bar",
            "title": f"Pass Percentage - {title}",
            "labels": labels,
            "datasets": [{
                "label": "Pass Percentage (%)",
                "data": pass_rates,
                "backgroundColor": "#EF4444" if is_toughest else "#10B981"
            }]
        }

        return {"answer": answer, "kpis": {"Category": title}, "chart": chart}

    def _format_toppers(self, rows, q):
        if not rows:
            return {"answer": "No students found matching ranking criteria."}

        answer = f"🏆 **Academic Rank List & Top Scorers**\n\n"
        top_student = rows[0]
        answer += f"🥇 **Top Ranker:** **{top_student.get('student_name')}** ({top_student.get('roll_no')}) with **{top_student.get('percentage')}%** (SGPA: {top_student.get('sgpa')})\n\n"
        
        answer += "| Rank | Roll No | Student Name | Dept | Sem | Percentage | SGPA | Status |\n"
        answer += "|---|---|---|---|---|---|---|---|\n"
        for idx, r in enumerate(rows, 1):
            answer += f"| #{idx} | **{r.get('roll_no')}** | {r.get('student_name')} | {r.get('dept_code')} | Sem {r.get('semester')} | **{r.get('percentage')}%** | {r.get('sgpa')} | {r.get('result_status')} |\n"

        labels = [r.get('student_name').split()[0] + f" ({r.get('roll_no')})" for r in rows[:10]]
        percentages = [r.get('percentage') for r in rows[:10]]

        chart = {
            "type": "bar",
            "title": "Top Students Score Comparison (%)",
            "labels": labels,
            "datasets": [{
                "label": "Percentage (%)",
                "data": percentages,
                "backgroundColor": "#F59E0B"
            }]
        }

        kpis = {
            "College Topper": top_student.get('student_name'),
            "Highest Percentage": f"{top_student.get('percentage')}%",
            "Highest SGPA": top_student.get('sgpa')
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_subject_topper(self, rows, q):
        if not rows:
            return {"answer": "No records found for this subject."}
        
        top = rows[0]
        subj = top.get('subject_name')
        code = top.get('subject_code')

        answer = (
            f"🏅 **Top Scorer in {subj} ({code})**\n\n"
            f"The highest mark was achieved by **{top.get('student_name')}** ({top.get('roll_no')}) "
            f"with a score of **{top.get('total_marks')} / 100** (Grade: {top.get('grade')}).\n"
            f"- Internal Marks: {top.get('internal_marks')} / 30\n"
            f"- External Marks: {top.get('external_marks')} / 70\n"
        )

        labels = [r.get('student_name') for r in rows]
        scores = [r.get('total_marks') for r in rows]

        chart = {
            "type": "bar",
            "title": f"Top Scorers in {code}",
            "labels": labels,
            "datasets": [{
                "label": "Total Marks",
                "data": scores,
                "backgroundColor": "#8B5CF6"
            }]
        }

        return {"answer": answer, "kpis": {"Top Score": f"{top.get('total_marks')}/100", "Topper": top.get('student_name')}, "chart": chart}

    def _format_failed_students(self, rows, q):
        if not rows:
            return {"answer": "🎉 Great news! Zero students failed under these criteria. 100% pass rate!"}

        count = len(rows)
        answer = f"⚠️ **Backlog / Failure Report ({count} Students)**\n\n"
        answer += f"Found **{count} student records** with backlogs or failed subjects requiring academic attention.\n\n"

        return {
            "answer": answer,
            "kpis": {"Failing Records": count},
            "chart": None
        }

    def _format_student_report(self, rows, q):
        if not rows:
            return {"answer": "No student record found with the specified Roll Number or Name."}

        first = rows[0]
        name = first.get('student_name')
        roll = first.get('roll_no')
        dept = first.get('dept_code')
        sem = first.get('semester')
        sec = first.get('section')

        tot_obtained = sum(r.get('total_marks', 0) for r in rows)
        tot_max = len(rows) * 100
        overall_pct = round((tot_obtained * 100.0) / tot_max, 2) if tot_max else 0
        total_credits = sum(r.get('credits', 3) for r in rows)
        weighted_gp = sum(r.get('grade_point', 0) * r.get('credits', 3) for r in rows)
        sgpa = round(weighted_gp / total_credits, 2) if total_credits else 0
        backlogs = sum(1 for r in rows if r.get('is_passed') == 0)

        status = "Fail" if backlogs > 0 else ("Distinction" if overall_pct >= 75 else "First Class" if overall_pct >= 60 else "Pass")

        answer = (
            f"📄 **Student Academic Report Card: {name}**\n\n"
            f"- **Roll No:** `{roll}` | **Department:** {dept} | **Semester:** {sem} (Sec {sec})\n"
            f"- **Overall Percentage:** **{overall_pct}%**\n"
            f"- **SGPA:** **{sgpa} / 10.0**\n"
            f"- **Academic Status:** **{status}** ({backlogs} backlogs)\n\n"
            f"| Subject Code | Subject Name | Credits | Int / 30 | Ext / 70 | Total / 100 | Grade | Status |\n"
            f"|---|---|---|---|---|---|---|---|\n"
        )
        for r in rows:
            st_badge = "✅ Pass" if r.get('is_passed') == 1 else "❌ Backlog"
            answer += f"| **{r.get('subject_code')}** | {r.get('subject_name')} | {r.get('credits')} | {r.get('internal_marks')} | {r.get('external_marks')} | **{r.get('total_marks')}** | `{r.get('grade')}` | {st_badge} |\n"

        labels = [r.get('subject_code') for r in rows]
        scores = [r.get('total_marks') for r in rows]

        chart = {
            "type": "radar",
            "title": f"Subject Performance Profile for {name}",
            "labels": labels,
            "datasets": [{
                "label": "Marks (out of 100)",
                "data": scores,
                "backgroundColor": "rgba(59, 130, 246, 0.2)",
                "borderColor": "#3B82F6",
                "pointBackgroundColor": "#2563EB"
            }]
        }

        kpis = {
            "Student": name,
            "Roll No": roll,
            "Percentage": f"{overall_pct}%",
            "SGPA": sgpa,
            "Result": status
        }

        return {"answer": answer, "kpis": kpis, "chart": chart}

    def _format_grade_distribution(self, rows, q):
        if not rows:
            return {"answer": "No grade distribution records found."}

        labels = [r.get('result_status') for r in rows]
        counts = [r.get('student_count') for r in rows]

        answer = "🎓 **Overall Result & Grade Classification**\n\n"
        for r in rows:
            answer += f"- **{r.get('result_status')}:** {r.get('student_count')} students ({r.get('percentage_of_total')}%)\n"

        chart = {
            "type": "doughnut",
            "title": "Student Classification Distribution",
            "labels": labels,
            "datasets": [{
                "data": counts,
                "backgroundColor": ["#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EF4444"]
            }]
        }

        return {"answer": answer, "kpis": {"Categories": len(rows)}, "chart": chart}

    def _format_section_comparison(self, rows, q):
        if not rows:
            return {"answer": "No section data available."}
        
        labels = [f"{r.get('dept_code')} Sem {r.get('semester')} Sec {r.get('section')}" for r in rows]
        pass_rates = [r.get('pass_percentage') for r in rows]

        answer = "🏫 **Section-Wise Academic Comparison**\n\n"
        answer += "| Cohort | Total | Passed | Pass % | Avg Score % | Avg SGPA |\n"
        answer += "|---|---|---|---|---|---|\n"
        for r in rows:
            answer += f"| **{r.get('dept_code')} Sem {r.get('semester')} - Sec {r.get('section')}** | {r.get('total_students')} | {r.get('passed_students')} | **{r.get('pass_percentage')}%** | {r.get('average_percentage')}% | {r.get('average_sgpa')} |\n"

        chart = {
            "type": "bar",
            "title": "Pass Percentage by Section",
            "labels": labels,
            "datasets": [{
                "label": "Pass %",
                "data": pass_rates,
                "backgroundColor": "#3B82F6"
            }]
        }

        return {"answer": answer, "kpis": {"Sections": len(rows)}, "chart": chart}

    def _format_semester_comparison(self, rows, q):
        if not rows:
            return {"answer": "No semester comparison records found."}
        
        labels = [f"Semester {r.get('semester')}" for r in rows]
        pass_rates = [r.get('pass_percentage') for r in rows]

        answer = "📅 **Semester-Wise Performance Comparison**\n\n"
        for r in rows:
            answer += f"- **Semester {r.get('semester')}:** {r.get('pass_percentage')}% pass rate (Avg Score: {r.get('average_percentage')}%, Avg SGPA: {r.get('average_sgpa')})\n"

        chart = {
            "type": "bar",
            "title": "Semester Pass Rate Comparison",
            "labels": labels,
            "datasets": [{
                "label": "Pass %",
                "data": pass_rates,
                "backgroundColor": "#6366F1"
            }]
        }

        return {"answer": answer, "kpis": {"Semesters": len(rows)}, "chart": chart}

    def _default_formatter(self, rows, q, intent_type):
        if not rows:
            return {"answer": "The query executed successfully, but returned 0 rows matching your criteria."}

        count = len(rows)
        answer = f"Found **{count} record{'s' if count != 1 else ''}** matching your query:\n\n"
        kpis = {"Rows Returned": count}
        return {"answer": answer, "kpis": kpis, "chart": None}
