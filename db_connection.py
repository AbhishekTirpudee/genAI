"""Reusable MySQL connections and parameterized recruitment-result storage."""

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

_connection_pool: Any = None


class DatabaseConfigurationError(RuntimeError):
    """Raised when required MySQL settings are not configured."""


class DatabaseOperationError(RuntimeError):
    """Raised when a MySQL operation fails."""


def _get_connection_pool() -> Any:
    global _connection_pool
    if _connection_pool is not None:
        return _connection_pool

    required = ("MYSQL_HOST", "MYSQL_USER", "MYSQL_DATABASE")
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise DatabaseConfigurationError(
            "MySQL configuration is incomplete. Set: "
            + ", ".join(missing)
            + " in the project .env file."
        )

    try:
        from mysql.connector.pooling import MySQLConnectionPool
    except ImportError as exc:
        raise DatabaseConfigurationError(
            "MySQL Connector/Python is not installed in the selected "
            "environment. Install it with: python -m pip install "
            "mysql-connector-python"
        ) from exc

    try:
        _connection_pool = MySQLConnectionPool(
            pool_name="recruitment_pool",
            pool_size=5,
            host=os.environ["MYSQL_HOST"].strip(),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.environ["MYSQL_USER"].strip(),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.environ["MYSQL_DATABASE"].strip(),
        )
    except (ValueError, Exception) as exc:
        _connection_pool = None
        raise DatabaseOperationError(
            f"Could not initialize the MySQL connection pool: {exc}"
        ) from exc
    return _connection_pool


def get_db_connection() -> Any:
    """Get a reusable pooled connection or raise a clear configuration error."""
    pool = _get_connection_pool()
    try:
        return pool.get_connection()
    except Exception as exc:
        raise DatabaseOperationError(
            f"Could not connect to MySQL. Check that the server is running "
            f"and the credentials are valid: {exc}"
        ) from exc


def initialize_database(schema_path: str | Path | None = None) -> None:
    """Create the configured database tables from ``schema.sql``."""
    path = Path(schema_path) if schema_path else PROJECT_ROOT / "database" / "schema.sql"
    try:
        statements = [
            statement.strip()
            for statement in path.read_text(encoding="utf-8").split(";")
            if statement.strip()
        ]
    except OSError as exc:
        raise DatabaseOperationError(
            f"Could not read database schema at '{path}': {exc}"
        ) from exc

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)
        _migrate_dashboard_columns(cursor)
        connection.commit()
        cursor.close()
    except Exception as exc:
        connection.rollback()
        raise DatabaseOperationError(
            f"Could not initialize the MySQL schema: {exc}"
        ) from exc
    finally:
        connection.close()


def _migrate_dashboard_columns(cursor: Any) -> None:
    """Add dashboard fields when upgrading an earlier project schema."""
    database = os.environ["MYSQL_DATABASE"].strip()
    additions = {
        "jobs": {
            "job_title": "VARCHAR(255) NULL",
            "company_name": "VARCHAR(255) NULL",
            "required_skills": "JSON NULL",
            "experience_requirements": "TEXT NULL",
            "job_location": "VARCHAR(255) NULL",
        },
        "candidates": {
            "reviewer_status": (
                "VARCHAR(32) NOT NULL DEFAULT 'Under Review'"
            ),
        },
        "skill_matches": {
            "short_explanation": "TEXT NULL",
        },
    }
    for table, columns in additions.items():
        for column, definition in columns.items():
            cursor.execute(
                """SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                AND COLUMN_NAME = %s""",
                (database, table, column),
            )
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}"
                )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def persist_recruitment_state(state: dict[str, Any]) -> str:
    """Save a completed candidate assessment transactionally.

    All values are passed as SQL parameters; query text is never assembled from
    resume, job-description, or recruiter input.
    """
    job_description = str(state.get("job_description") or "")
    candidate = state.get("parsed_candidate_details") or {}
    skills = state.get("skills_comparison") or {}
    screening = state.get("screening_results") or {}
    questions = state.get("interview_questions") or []
    report = state.get("final_recruitment_report") or {}
    job_id = state.get("job_id") or hashlib.sha256(
        job_description.encode("utf-8")
    ).hexdigest()
    candidate_id = str(uuid.uuid4())

    connection = get_db_connection()
    try:
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT IGNORE INTO jobs (job_id, job_description)
            VALUES (%s, %s)""",
            (job_id, job_description),
        )
        cursor.execute(
            """INSERT INTO candidates
            (candidate_id, job_id, resume_file_name, candidate_name, email,
             phone_number, candidate_details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                candidate_id,
                job_id,
                state.get("resume_file_name"),
                candidate.get("candidate_name"),
                candidate.get("email"),
                candidate.get("phone_number"),
                _json(candidate),
            ),
        )
        cursor.execute(
            """INSERT INTO skill_matches
            (candidate_id, required_skills, candidate_skills, exact_matches,
             related_matches, missing_skills, matching_percentage, score_calculation,
             short_explanation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                candidate_id,
                _json(skills.get("required_skills", [])),
                _json(skills.get("candidate_skills", [])),
                _json(skills.get("exact_matched_skills", [])),
                _json(skills.get("related_matched_skills", [])),
                _json(skills.get("missing_skills", [])),
                skills.get("matching_percentage"),
                skills.get("score_calculation", ""),
                skills.get("short_explanation"),
            ),
        )
        cursor.execute(
            """INSERT INTO screening_reports
            (candidate_id, strengths, relevant_gaps, verification_areas, summary)
            VALUES (%s, %s, %s, %s, %s)""",
            (
                candidate_id,
                _json(screening.get("strengths", [])),
                _json(screening.get("relevant_gaps", [])),
                _json(screening.get("verification_areas", [])),
                screening.get("summary", ""),
            ),
        )
        cursor.execute(
            """INSERT INTO interview_questions (candidate_id, questions)
            VALUES (%s, %s)""",
            (candidate_id, _json(questions)),
        )
        cursor.execute(
            """INSERT INTO recruitment_reports
            (candidate_id, report_text, pdf_path)
            VALUES (%s, %s, %s)""",
            (
                candidate_id,
                report.get("report_text", ""),
                state.get("report_pdf_path"),
            ),
        )
        connection.commit()
        cursor.close()
        return candidate_id
    except Exception as exc:
        connection.rollback()
        raise DatabaseOperationError(
            f"Could not save recruitment results to MySQL: {exc}"
        ) from exc
    finally:
        connection.close()


def save_job(
    *,
    job_title: str,
    company_name: str,
    job_description: str,
    required_skills: list[str],
    experience_requirements: str,
    job_location: str,
) -> str:
    """Save a recruiter-created job and return its database ID."""
    if not job_title.strip() or not job_description.strip():
        raise ValueError("Job title and job description are required.")

    job_id = hashlib.sha256(
        f"{uuid.uuid4()}:{job_title}:{job_description}".encode("utf-8")
    ).hexdigest()
    description_parts = [job_description.strip()]
    if required_skills:
        description_parts.append(
            "Required technical skills: " + ", ".join(required_skills)
        )
    if experience_requirements.strip():
        description_parts.append(
            "Experience requirements: " + experience_requirements.strip()
        )
    if job_location.strip():
        description_parts.append("Job location: " + job_location.strip())
    full_description = "\n\n".join(description_parts)

    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO jobs
            (job_id, job_description, job_title, company_name, required_skills,
             experience_requirements, job_location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                job_id,
                full_description,
                job_title.strip(),
                company_name.strip() or None,
                _json(required_skills),
                experience_requirements.strip() or None,
                job_location.strip() or None,
            ),
        )
        connection.commit()
        cursor.close()
        return job_id
    except Exception as exc:
        connection.rollback()
        raise DatabaseOperationError(f"Could not save the job: {exc}") from exc
    finally:
        connection.close()


def _decode_json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def list_jobs() -> list[dict[str, Any]]:
    """Return saved jobs for recruiter selection."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT job_id, job_title, company_name, job_description,
            required_skills, experience_requirements, job_location, created_at
            FROM jobs ORDER BY created_at DESC"""
        )
        jobs = cursor.fetchall()
        cursor.close()
        for job in jobs:
            job["required_skills"] = _decode_json(
                job.get("required_skills"), []
            )
        return jobs
    except Exception as exc:
        raise DatabaseOperationError(f"Could not load saved jobs: {exc}") from exc
    finally:
        connection.close()


def get_dashboard_data(recent_limit: int = 10) -> dict[str, Any]:
    """Return dashboard metrics and recent candidate activity from MySQL."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS total_candidates FROM candidates")
        total_candidates = cursor.fetchone()["total_candidates"]
        cursor.execute(
            """SELECT COUNT(*) AS total_jobs FROM jobs
            WHERE job_title IS NOT NULL AND job_title <> ''"""
        )
        total_jobs = cursor.fetchone()["total_jobs"]
        cursor.execute(
            "SELECT AVG(matching_percentage) AS average_score FROM skill_matches"
        )
        average_score = cursor.fetchone()["average_score"]
        cursor.execute(
            """SELECT COUNT(*) AS awaiting_review FROM candidates
            WHERE reviewer_status = %s""",
            ("Under Review",),
        )
        awaiting_review = cursor.fetchone()["awaiting_review"]
        cursor.execute(
            """SELECT c.candidate_id, c.candidate_name, c.email,
            c.resume_file_name, c.reviewer_status, c.created_at,
            sm.matching_percentage, j.job_title, j.company_name
            FROM candidates c
            LEFT JOIN skill_matches sm ON sm.candidate_id = c.candidate_id
            LEFT JOIN jobs j ON j.job_id = c.job_id
            ORDER BY c.created_at DESC LIMIT %s""",
            (recent_limit,),
        )
        recent_candidates = cursor.fetchall()
        cursor.close()
        return {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "average_score": (
                float(average_score) if average_score is not None else None
            ),
            "awaiting_review": awaiting_review,
            "recent_candidates": recent_candidates,
        }
    except Exception as exc:
        raise DatabaseOperationError(
            f"Could not load dashboard data: {exc}"
        ) from exc
    finally:
        connection.close()


def list_candidates(limit: int = 200) -> list[dict[str, Any]]:
    """Return candidate summaries with their linked job and skills score."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.candidate_id, c.candidate_name, c.email,
            c.phone_number, c.resume_file_name, c.reviewer_status,
            c.created_at, sm.matching_percentage, j.job_title, j.company_name
            FROM candidates c
            LEFT JOIN skill_matches sm ON sm.candidate_id = c.candidate_id
            LEFT JOIN jobs j ON j.job_id = c.job_id
            ORDER BY c.created_at DESC LIMIT %s""",
            (limit,),
        )
        candidates = cursor.fetchall()
        cursor.close()
        return candidates
    except Exception as exc:
        raise DatabaseOperationError(f"Could not load candidates: {exc}") from exc
    finally:
        connection.close()


def get_candidate_details(candidate_id: str) -> dict[str, Any] | None:
    """Return one candidate and all stored analysis results."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT c.candidate_id, c.resume_file_name, c.candidate_name,
            c.email, c.phone_number, c.candidate_details, c.reviewer_status,
            c.created_at, j.job_id, j.job_title, j.company_name,
            j.job_description, sm.required_skills, sm.candidate_skills,
            sm.exact_matches, sm.related_matches, sm.missing_skills,
            sm.matching_percentage, sm.score_calculation,
            sm.short_explanation,
            sr.strengths, sr.relevant_gaps, sr.verification_areas, sr.summary
                AS screening_summary,
            iq.questions, rr.report_text, rr.pdf_path
            FROM candidates c
            LEFT JOIN jobs j ON j.job_id = c.job_id
            LEFT JOIN skill_matches sm ON sm.candidate_id = c.candidate_id
            LEFT JOIN screening_reports sr ON sr.candidate_id = c.candidate_id
            LEFT JOIN interview_questions iq ON iq.candidate_id = c.candidate_id
            LEFT JOIN recruitment_reports rr ON rr.candidate_id = c.candidate_id
            WHERE c.candidate_id = %s""",
            (candidate_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None
        json_defaults = {
            "candidate_details": {},
            "required_skills": [],
            "candidate_skills": [],
            "exact_matches": [],
            "related_matches": [],
            "missing_skills": [],
            "strengths": [],
            "relevant_gaps": [],
            "verification_areas": [],
            "questions": [],
        }
        for key, default in json_defaults.items():
            row[key] = _decode_json(row.get(key), default)
        return row
    except Exception as exc:
        raise DatabaseOperationError(
            f"Could not load candidate analysis: {exc}"
        ) from exc
    finally:
        connection.close()


def update_reviewer_status(candidate_id: str, status: str) -> None:
    """Save the review decision selected by a recruiter."""
    allowed = {"Shortlisted", "Under Review", "Not Selected"}
    if status not in allowed:
        raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}.")
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE candidates SET reviewer_status = %s WHERE candidate_id = %s",
            (status, candidate_id),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT candidate_id FROM candidates WHERE candidate_id = %s",
                (candidate_id,),
            )
            if cursor.fetchone() is None:
                raise DatabaseOperationError(
                    f"No candidate found with ID '{candidate_id}'."
                )
        connection.commit()
        cursor.close()
    except Exception as exc:
        connection.rollback()
        if isinstance(exc, DatabaseOperationError):
            raise
        raise DatabaseOperationError(
            f"Could not update recruiter decision: {exc}"
        ) from exc
    finally:
        connection.close()


def check_database_connection() -> None:
    """Verify configured MySQL connectivity without returning any data."""
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
    except Exception as exc:
        raise DatabaseOperationError(
            f"Could not verify the MySQL connection: {exc}"
        ) from exc
    finally:
        connection.close()
