"""
Flask Web Application & API Server for College Result Analysis Agent.
Provides REST APIs for conversational query processing, dashboard statistics,
student marksheets, SQL playground, and database schema explorer.
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add root directory of agent to python path
sys.path.insert(0, os.path.dirname(__file__))

from database.db import execute_safe_query, get_schema_summary, get_db_connection
from agent.query_engine import ResultAnalysisAgent
from agent.safety import sanitize_and_validate_sql

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER)
CORS(app)

# Initialize Agent
agent = ResultAnalysisAgent()

# -------------------------------------------------------------------
# Static Web App Routes
# -------------------------------------------------------------------
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# -------------------------------------------------------------------
# API Routes
# -------------------------------------------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "College Result Analysis Agent",
        "version": "1.0.0"
    })

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    Main Natural Language Agent Endpoint.
    Expects JSON: { "question": str, "api_key": optional str, "provider": optional str }
    """
    payload = request.get_json(force=True, silent=True) or {}
    question = payload.get('question', '').strip()
    api_key = payload.get('api_key')
    provider = payload.get('provider')

    if not question:
        return jsonify({
            "success": False,
            "error": "Question parameter is required."
        }), 400

    # If custom key supplied in request, instantiate temporary agent with key
    active_agent = ResultAnalysisAgent(api_key=api_key, provider=provider) if api_key else agent
    result = active_agent.process_query(question)
    return jsonify(result)

@app.route('/api/sql/execute', methods=['POST'])
def execute_sql_endpoint():
    """
    Direct SQL Query Execution (Read-Only Safe).
    Expects JSON: { "sql": str }
    """
    payload = request.get_json(force=True, silent=True) or {}
    raw_sql = payload.get('sql', '').strip()

    is_valid, clean_sql, error_msg = sanitize_and_validate_sql(raw_sql)
    if not is_valid:
        return jsonify({
            "success": False,
            "error": error_msg,
            "columns": [],
            "rows": []
        }), 400

    result = execute_safe_query(clean_sql)
    return jsonify(result)

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Returns overview metrics, department stats, subject performance, and grade distributions."""
    try:
        # 1. Overall Metrics
        overall_res = execute_safe_query("""
            SELECT 
                COUNT(*) AS total_students,
                SUM(CASE WHEN result_status != 'Fail' THEN 1 ELSE 0 END) AS passed_students,
                SUM(CASE WHEN result_status = 'Fail' THEN 1 ELSE 0 END) AS failed_students,
                ROUND(SUM(CASE WHEN result_status != 'Fail' THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(*), 2) AS pass_percentage,
                ROUND(AVG(percentage), 2) AS college_average_percentage,
                ROUND(AVG(sgpa), 2) AS college_average_sgpa
            FROM v_student_summary
        """)

        # 2. Department Breakdown
        dept_res = execute_safe_query("""
            SELECT dept_code, dept_name, total_students, passed_students, failed_students,
                   pass_percentage, average_percentage, average_sgpa
            FROM v_department_performance
            ORDER BY pass_percentage DESC
        """)

        # 3. Subject Performance
        subject_res = execute_safe_query("""
            SELECT subject_code, subject_name, dept_code, semester, credits,
                   total_appeared, passed_count, failed_count, pass_percentage,
                   average_marks, highest_marks, lowest_marks
            FROM v_subject_performance
            ORDER BY pass_percentage DESC
        """)

        # 4. Grade Distribution
        grade_res = execute_safe_query("""
            SELECT result_status, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM v_student_summary), 2) as percentage
            FROM v_student_summary
            GROUP BY result_status
            ORDER BY 
                CASE result_status
                    WHEN 'Distinction' THEN 1
                    WHEN 'First Class' THEN 2
                    WHEN 'Second Class' THEN 3
                    WHEN 'Pass Class' THEN 4
                    ELSE 5
                END
        """)

        # 5. Top 5 Rankers
        toppers_res = execute_safe_query("""
            SELECT roll_no, student_name, dept_code, semester, section, percentage, sgpa, result_status
            FROM v_student_summary
            WHERE result_status != 'Fail'
            ORDER BY percentage DESC, sgpa DESC
            LIMIT 5
        """)

        return jsonify({
            "success": True,
            "overall": overall_res['rows'][0] if overall_res['rows'] else {},
            "departments": dept_res['rows'],
            "subjects": subject_res['rows'],
            "grades": grade_res['rows'],
            "toppers": toppers_res['rows']
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/students', methods=['GET'])
def list_students():
    """List and search students with filters (dept, semester, search text)."""
    dept = request.args.get('dept')
    semester = request.args.get('semester')
    search = request.args.get('search', '').strip()

    conditions = []
    params = []

    if dept:
        conditions.append("dept_code = ?")
        params.append(dept)
    if semester:
        conditions.append("semester = ?")
        params.append(semester)
    if search:
        conditions.append("(UPPER(roll_no) LIKE ? OR UPPER(student_name) LIKE ? OR UPPER(usn) LIKE ?)")
        params.extend([f"%{search.upper()}%", f"%{search.upper()}%", f"%{search.upper()}%"])

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"""
        SELECT student_id, roll_no, usn, student_name, gender, dept_code, semester, section,
               total_marks_obtained, total_max_marks, percentage, sgpa, subjects_failed, result_status
        FROM v_student_summary
        {where_clause}
        ORDER BY roll_no ASC
        LIMIT 100
    """
    res = execute_safe_query(sql, tuple(params))
    return jsonify(res)

@app.route('/api/student/<roll_no>', methods=['GET'])
def get_student_details(roll_no):
    """Retrieve full transcript and marksheet for a student by roll number."""
    # Summary
    summary_res = execute_safe_query("""
        SELECT * FROM v_student_summary WHERE UPPER(roll_no) = UPPER(?)
    """, (roll_no,))
    
    if not summary_res['rows']:
        return jsonify({"success": False, "error": f"Student with roll number '{roll_no}' not found."}), 404

    # Subject-wise marks
    marks_res = execute_safe_query("""
        SELECT subject_code, subject_name, credits, pass_marks,
               internal_marks, external_marks, total_marks, grade, grade_point, is_passed
        FROM v_student_marks
        WHERE UPPER(roll_no) = UPPER(?)
        ORDER BY subject_code ASC
    """, (roll_no,))

    return jsonify({
        "success": True,
        "student": summary_res['rows'][0],
        "marks": marks_res['rows']
    })

@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Returns database schema definition."""
    try:
        schema = get_schema_summary()
        return jsonify({"success": True, "schema": schema})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    port = int(os.environ.get('PORT', 5050))
    print(f"[*] College Result Analysis Agent starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
