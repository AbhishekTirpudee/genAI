"""Streamlit recruiter dashboard backed by LangGraph and MySQL."""

import html
import sys
from uuid import uuid4
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.report_agent import ReportAgentError, create_pdf_report
from database.db_connection import (
    DatabaseConfigurationError,
    DatabaseOperationError,
    check_database_connection,
    get_candidate_details,
    get_dashboard_data,
    initialize_database,
    list_candidates,
    list_jobs,
    save_job,
    update_reviewer_status,
)
from workflow.graph import format_workflow_error, run_recruitment_process

PAGES = (
    "Resume Upload",
    "Skills Matching",
    "Resume Screening",
    "Interview Questions",
    "Candidate Reports",
    "Dashboard",
    "Job Management",
)
REVIEW_STATUSES = ("Shortlisted", "Under Review", "Not Selected")

st.set_page_config(
    page_title="TalentDesk | Recruitment",
    page_icon="♢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #11233f;
        --blue: #244b7a;
        --accent: #527cac;
        --paper: #ffffff;
        --canvas: #f3f6fa;
        --ink: #1c2b3a;
        --muted: #6b7787;
        --line: #e3e9f0;
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    [data-testid="stSidebar"] {
        background: var(--navy);
        border-right: 1px solid #263b58;
    }
    [data-testid="stSidebar"] * { color: #eef4fb; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #17283e; }
    .brand {
        font-size: 1.35rem; font-weight: 750; letter-spacing: .02em;
        color: #ffffff; padding: .5rem 0 .1rem;
    }
    .brand-subtitle {
        color: #b6c6d9; font-size: .82rem; margin-bottom: 1.6rem;
    }
    .page-kicker {
        color: var(--accent); text-transform: uppercase; letter-spacing: .12em;
        font-size: .75rem; font-weight: 700; margin-bottom: .3rem;
    }
    .page-title {
        color: var(--navy); font-size: 2rem; font-weight: 750;
        margin: 0 0 .35rem;
    }
    .page-description { color: var(--muted); margin-bottom: 1.35rem; }
    .metric-card {
        background: var(--paper); border: 1px solid var(--line);
        border-radius: 14px; padding: 1rem 1.15rem; min-height: 116px;
        box-shadow: 0 3px 14px rgba(17,35,63,.045);
    }
    .metric-label { color: var(--muted); font-size: .82rem; }
    .metric-value { color: var(--navy); font-size: 1.8rem; font-weight: 750; }
    .metric-note { color: var(--muted); font-size: .75rem; }
    .panel {
        background: var(--paper); border: 1px solid var(--line);
        border-radius: 14px; padding: 1.1rem 1.2rem;
        box-shadow: 0 3px 14px rgba(17,35,63,.035);
    }
    .empty-state {
        background: #ffffff; border: 1px dashed #cbd6e2; border-radius: 14px;
        color: #536274; padding: 1.25rem; margin: .75rem 0;
    }
    div.stButton > button[kind="primary"] {
        background: var(--blue); border-color: var(--blue);
        border-radius: 9px; font-weight: 650;
    }
    div.stButton > button { border-radius: 9px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _page_header(title: str, description: str) -> None:
    st.markdown(
        f'<div class="page-kicker">TalentDesk · Recruitment Intelligence</div>'
        f'<div class="page-title">{title}</div>'
        f'<div class="page-description">{description}</div>',
        unsafe_allow_html=True,
    )


def _database_error() -> str | None:
    try:
        check_database_connection()
    except (DatabaseConfigurationError, DatabaseOperationError) as exc:
        return str(exc)
    return None


def _render_database_setup() -> None:
    with st.expander("Database setup and connection", expanded=False):
        error = _database_error()
        if error:
            st.warning(error)
            st.caption(
                "Configure MYSQL_HOST, MYSQL_PORT, MYSQL_USER, "
                "MYSQL_PASSWORD, and MYSQL_DATABASE in the project .env. "
                "The target MySQL database must already exist."
            )
        else:
            st.success("Connected to the configured MySQL server.")
        if st.button("Initialize / update database tables", key="init_database"):
            try:
                initialize_database()
                st.success("Database tables are ready.")
                st.rerun()
            except (DatabaseConfigurationError, DatabaseOperationError) as exc:
                st.error(f"Could not initialize the database: {exc}")


def _fetch_jobs() -> list[dict[str, Any]] | None:
    error = _database_error()
    if error:
        st.warning(f"MySQL is unavailable: {error}")
        return None
    try:
        return list_jobs()
    except DatabaseOperationError as exc:
        st.error(f"Could not load jobs: {exc}")
        st.info("Initialize the project database tables before continuing.")
        return None


def _records() -> list[dict[str, Any]] | None:
    records: list[dict[str, Any]] = []
    try:
        candidates = list_candidates()
    except DatabaseOperationError as exc:
        candidates = []
        if not st.session_state.get("analysis_results"):
            st.info(
                f"Saved candidate history is unavailable: {exc} "
                "Session-only analyses remain available until this browser session ends."
            )
    except DatabaseConfigurationError as exc:
        candidates = []
        if not st.session_state.get("analysis_results"):
            st.info(
                f"MySQL is not configured: {exc} "
                "Session-only analyses remain available until this browser session ends."
            )
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    for result in st.session_state.get("analysis_results", []):
        candidate_id = result.get("database_candidate_id") or result.get(
            "_session_candidate_id"
        )
        if candidate_id:
            row = by_id.setdefault(
                candidate_id,
                {
                    "candidate_id": candidate_id,
                    "candidate_name": (
                        result.get("parsed_candidate_details") or {}
                    ).get("candidate_name"),
                    "resume_file_name": result.get("resume_file_name"),
                    "reviewer_status": result.get(
                        "_reviewer_status", "Under Review"
                    ),
                    "job_title": result.get("job_title") or "Current analysis",
                },
            )
            row["_workflow_state"] = result
    records = list(by_id.values())
    return records


def _load_assessment(candidate_row: dict[str, Any]) -> dict[str, Any] | None:
    workflow_state = candidate_row.get("_workflow_state")
    if workflow_state:
        return {
            "candidate_id": candidate_row["candidate_id"],
            "candidate_details": workflow_state.get("parsed_candidate_details") or {},
            "resume_file_name": workflow_state.get("resume_file_name"),
            "reviewer_status": workflow_state.get(
                "_reviewer_status",
                candidate_row.get("reviewer_status", "Under Review"),
            ),
            "job_title": workflow_state.get("job_title")
            or candidate_row.get("job_title"),
            "company_name": workflow_state.get("company_name")
            or candidate_row.get("company_name"),
            "job_description": workflow_state.get("job_description"),
            "skills_comparison": workflow_state.get("skills_comparison") or {},
            "screening_results": workflow_state.get("screening_results") or {},
            "interview_questions": workflow_state.get("interview_questions") or [],
            "report": workflow_state.get("final_recruitment_report") or {},
            "pdf_bytes": workflow_state.get("report_pdf_bytes"),
        }
    try:
        stored = get_candidate_details(candidate_row["candidate_id"])
    except DatabaseOperationError as exc:
        st.error(f"Could not load this candidate's analysis: {exc}")
        return None
    if stored is None:
        st.warning("The candidate record no longer exists.")
        return None
    return {
        "candidate_id": stored["candidate_id"],
        "candidate_details": stored["candidate_details"],
        "resume_file_name": stored["resume_file_name"],
        "reviewer_status": stored["reviewer_status"],
        "job_title": stored.get("job_title"),
        "company_name": stored.get("company_name"),
        "job_description": stored.get("job_description"),
        "skills_comparison": {
            "required_skills": stored["required_skills"],
            "candidate_skills": stored["candidate_skills"],
            "exact_matched_skills": stored["exact_matches"],
            "related_matched_skills": stored["related_matches"],
            "missing_skills": stored["missing_skills"],
            "matching_percentage": (
                float(stored["matching_percentage"])
                if stored.get("matching_percentage") is not None
                else None
            ),
            "score_calculation": stored.get("score_calculation"),
            "short_explanation": stored.get("short_explanation"),
        },
        "screening_results": {
            "strengths": stored["strengths"],
            "relevant_gaps": stored["relevant_gaps"],
            "verification_areas": stored["verification_areas"],
            "summary": stored.get("screening_summary"),
        },
        "interview_questions": stored["questions"],
        "report": {"report_text": stored.get("report_text") or ""},
        "pdf_path": stored.get("pdf_path"),
    }


def _candidate_selector(
    page_records: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if not page_records:
        st.markdown(
            '<div class="empty-state">No completed candidate analyses are available yet. '
            'Upload resumes and run the recruitment workflow to populate this page.</div>',
            unsafe_allow_html=True,
        )
        return None
    labels = {
        row["candidate_id"]: (
            f"{row.get('candidate_name') or row.get('resume_file_name') or 'Candidate'}"
            f" · {row.get('job_title') or 'Saved assessment'}"
            f" · {row['candidate_id'][:8]}"
        )
        for row in page_records
    }
    selected_id = st.selectbox(
        "Select candidate",
        options=list(labels),
        format_func=lambda value: labels[value],
        key=f"candidate_{st.session_state.get('navigation', '')}",
    )
    selected = next(row for row in page_records if row["candidate_id"] == selected_id)
    return _load_assessment(selected)


def _show_skill_comparison(skills: dict[str, Any]) -> None:
    score = skills.get("matching_percentage")
    if score is None:
        st.info("No explicit required skills were found; no percentage was calculated.")
    else:
        st.progress(max(0, min(100, int(round(score)))))
        st.metric("Skills match", f"{score:.1f}%")
        if skills.get("score_calculation"):
            st.caption(f"Score formula: {skills['score_calculation']}")
    st.markdown("**Exact matches**")
    exact = skills.get("exact_matched_skills") or []
    st.write(", ".join(item["required_skill"] for item in exact) if exact else "None")
    st.markdown("**Related matches**")
    related = skills.get("related_matched_skills") or []
    if related:
        st.dataframe(
            [
                {
                    "Required skill": item["required_skill"],
                    "Resume skill": item["candidate_skill"],
                    "Cosine similarity": item.get("similarity"),
                }
                for item in related
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.write("None")
    st.markdown("**Required skills without a match**")
    missing = skills.get("missing_skills") or []
    st.write(", ".join(missing) if missing else "None")
    if skills.get("short_explanation"):
        st.info(skills["short_explanation"])


def _dashboard() -> None:
    _page_header(
        "Recruitment dashboard",
        "A live view of candidates, job openings, and recruiter review progress.",
    )
    error = _database_error()
    if error:
        st.markdown(
            '<div class="empty-state"><strong>Dashboard data is not connected.</strong>'
            '<br>Configure MySQL to view real candidate and job statistics. '
            'No sample statistics are shown.</div>',
            unsafe_allow_html=True,
        )
        st.caption(error)
        _render_database_setup()
        return
    try:
        data = get_dashboard_data()
    except DatabaseOperationError as exc:
        st.warning("The database is reachable, but dashboard tables are not ready.")
        st.caption(str(exc))
        _render_database_setup()
        return

    cols = st.columns(4)
    metrics = (
        ("Candidates processed", data["total_candidates"], "Stored analyses"),
        ("Jobs created", data["total_jobs"], "Recruiter-created roles"),
        (
            "Average skills match",
            (
                f"{data['average_score']:.1f}%"
                if data["average_score"] is not None
                else "—"
            ),
            "Across scored candidates",
        ),
        ("Awaiting review", data["awaiting_review"], "Under Review"),
    )
    for col, (label, value, note) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{value}</div>'
                f'<div class="metric-note">{note}</div></div>',
                unsafe_allow_html=True,
            )

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Candidate matching scores")
        scores = [
            {
                "Candidate": row.get("candidate_name")
                or row.get("resume_file_name")
                or "Candidate",
                "Match (%)": float(row["matching_percentage"]),
            }
            for row in data["recent_candidates"]
            if row.get("matching_percentage") is not None
        ]
        if scores:
            st.bar_chart(scores, x="Candidate", y="Match (%)", color="#244b7a")
        else:
            st.markdown(
                '<div class="empty-state">No candidate score data yet.</div>',
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Recent recruitment activity")
        if data["recent_candidates"]:
            for candidate in data["recent_candidates"][:5]:
                name = candidate.get("candidate_name") or candidate.get(
                    "resume_file_name"
                )
                job = candidate.get("job_title") or "Job not specified"
                score = candidate.get("matching_percentage")
                score_label = f"{float(score):.0f}% match" if score is not None else "Not scored"
                st.markdown(
                    f'<div class="panel" style="margin-bottom:.55rem">'
                    f'<strong>{html.escape(str(name))}</strong><br>'
                    f'<span style="color:#6b7787">'
                    f'{html.escape(str(job))} · {html.escape(score_label)}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="empty-state">No recruitment activity has been recorded.</div>',
                unsafe_allow_html=True,
            )

    st.subheader("Recent candidate analyses")
    if data["recent_candidates"]:
        st.dataframe(
            [
                {
                    "Candidate": row.get("candidate_name") or "Name not provided",
                    "Resume": row.get("resume_file_name"),
                    "Job": row.get("job_title") or "—",
                    "Match": (
                        f"{float(row['matching_percentage']):.1f}%"
                        if row.get("matching_percentage") is not None
                        else "—"
                    ),
                    "Recruiter status": row.get("reviewer_status"),
                    "Created": row.get("created_at"),
                }
                for row in data["recent_candidates"]
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.markdown(
            '<div class="empty-state">No candidates have been processed yet.</div>',
            unsafe_allow_html=True,
        )


def _job_management() -> None:
    _page_header(
        "Job management",
        "Create and review the job descriptions used for candidate analysis.",
    )
    _render_database_setup()
    with st.form("create_job"):
        st.subheader("Create a job")
        title = st.text_input("Job title *")
        company = st.text_input("Company name")
        description = st.text_area("Job description *", height=180)
        skills = st.text_input(
            "Required technical skills",
            placeholder="Python, FastAPI, MySQL",
        )
        experience = st.text_input("Experience requirements")
        location = st.text_input("Job location")
        submitted = st.form_submit_button("Save job", type="primary")
    if submitted:
        required_skills = [item.strip() for item in skills.split(",") if item.strip()]
        try:
            job_id = save_job(
                job_title=title,
                company_name=company,
                job_description=description,
                required_skills=required_skills,
                experience_requirements=experience,
                job_location=location,
            )
            st.success(f"Job saved. Reference: {job_id[:12]}")
        except ValueError as exc:
            st.error(str(exc))
        except (DatabaseConfigurationError, DatabaseOperationError) as exc:
            st.error(f"Could not save this job: {exc}")

    st.subheader("Saved jobs")
    jobs = _fetch_jobs()
    if jobs:
        st.dataframe(
            [
                {
                    "Job title": job.get("job_title") or "Untitled",
                    "Company": job.get("company_name") or "—",
                    "Required skills": ", ".join(job.get("required_skills") or []),
                    "Experience": job.get("experience_requirements") or "—",
                    "Location": job.get("job_location") or "—",
                    "Created": job.get("created_at"),
                }
                for job in jobs
            ],
            hide_index=True,
            use_container_width=True,
        )
    elif jobs == []:
        st.info("No jobs have been created yet.")


def _resume_upload() -> None:
    _page_header(
        "Run recruitment analysis",
        "Upload a resume and provide the job description. The five-agent workflow "
        "will parse, compare, screen, prepare questions, and create a report.",
    )
    stage_columns = st.columns(5)
    for column, (number, title) in zip(
        stage_columns,
        (
            ("01", "Parse resume"),
            ("02", "Match skills"),
            ("03", "Screen evidence"),
            ("04", "Create questions"),
            ("05", "Generate report"),
        ),
    ):
        with column:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">STEP {number}'
                f'</div><strong>{title}</strong></div>',
                unsafe_allow_html=True,
            )
    st.markdown("#### 1 · Job details")
    job_title = st.text_input(
        "Job title (optional)",
        placeholder="e.g. Python Backend Engineer",
        key="analysis_job_title",
    )
    job_description = st.text_area(
        "Paste the job description *",
        height=190,
        placeholder=(
            "Include responsibilities, required technical skills, experience, "
            "and qualifications..."
        ),
        key="analysis_job_description",
    )

    st.markdown("#### 2 · Candidate resumes")
    uploads = st.file_uploader(
        "Upload PDF or DOCX resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Text-based PDFs and DOCX files are supported.",
        key="analysis_resume_uploads",
    )
    if uploads:
        st.markdown("**Selected files**")
        for upload in uploads:
            st.write(f"• {upload.name} · {upload.size:,} bytes")
    st.caption(
        "Demo mode keeps results in this browser session. No database is required."
    )
    if not st.button(
        "Start recruitment analysis",
        type="primary",
        disabled=not uploads or not job_description.strip(),
        key="start_recruitment_analysis",
    ):
        return

    invalid = [
        upload.name
        for upload in uploads
        if Path(upload.name).suffix.lower() not in {".pdf", ".docx"}
        or upload.size == 0
    ]
    if invalid:
        st.error(
            "These files are empty or have an unsupported format: "
            + ", ".join(invalid)
        )
        return
    progress = st.progress(0, text="Preparing analysis...")
    status = st.empty()
    stage_labels = {
        "resume_parsing_agent": "Parsing resume",
        "skills_matching_agent": "Matching skills",
        "resume_screening_agent": "Screening evidence",
        "interview_question_agent": "Preparing interview questions",
        "recruitment_report_agent": "Generating report and saving results",
    }
    total_steps = max(1, len(uploads) * 5)

    def update_progress(node: str, candidate_index: int, total_candidates: int) -> None:
        step_index = (candidate_index - 1) * 5 + (
            list(stage_labels).index(node) + 1 if node in stage_labels else 0
        )
        fraction = min(1.0, step_index / total_steps)
        progress.progress(
            fraction,
            text=f"Candidate {candidate_index} of {total_candidates}: "
            f"{stage_labels.get(node, node)}",
        )
        status.info(f"Running {stage_labels.get(node, node)}...")

    try:
        results = run_recruitment_process(
            [(upload.name, upload.getvalue()) for upload in uploads],
            job_description,
            pdf_output_dir=PROJECT_ROOT / "reports",
            persist_to_database=False,
            progress_callback=update_progress,
        )
    except (DatabaseConfigurationError, DatabaseOperationError) as exc:
        status.empty()
        st.error(f"Database error: {exc}")
        return
    except Exception as exc:
        status.empty()
        st.error(
            "Could not execute the recruitment workflow: "
            f"{format_workflow_error(exc)}"
        )
        return

    for result in results:
        result["job_title"] = job_title
        result["company_name"] = None
        if not result.get("database_candidate_id"):
            result["_session_candidate_id"] = str(uuid4())
        result.setdefault("_reviewer_status", "Under Review")
    st.session_state["analysis_results"] = results + st.session_state.get(
        "analysis_results", []
    )
    progress.progress(1.0, text="Analysis finished.")
    status.empty()
    for result in results:
        if result.get("workflow_status") == "completed":
            st.success(
                f"{result.get('resume_file_name')}: analysis completed and saved."
            )
            if result.get("report_pdf_path"):
                st.caption(f"PDF report: {result['report_pdf_path']}")
        else:
            st.error(
                f"{result.get('resume_file_name')}: "
                + "; ".join(
                    format_workflow_error(message)
                    for message in result.get(
                        "error_messages", ["Analysis failed."]
                    )
                )
            )
    for result in results:
        if result.get("workflow_status") == "completed":
            _display_analysis_result(result)


def _display_analysis_result(result: dict[str, Any]) -> None:
    details = result.get("parsed_candidate_details") or {}
    candidate_name = (
        details.get("candidate_name") or result.get("resume_file_name") or "Candidate"
    )
    st.markdown("---")
    st.subheader(f"Analysis results · {candidate_name}")
    st.caption(result.get("job_title") or "Job description provided for this analysis")
    skills = result.get("skills_comparison") or {}
    _show_skill_comparison(skills)

    st.markdown("### Interview questions from this resume")
    questions = result.get("interview_questions") or []
    for difficulty in ("beginner", "intermediate", "advanced"):
        with st.expander(f"{difficulty.title()} questions", expanded=difficulty == "beginner"):
            grouped = [
                question
                for question in questions
                if question.get("difficulty") == difficulty
            ]
            if not grouped:
                st.write("No questions at this difficulty were generated.")
            for index, question in enumerate(grouped, start=1):
                category = question.get("category", "technical").title()
                st.markdown(f"**{index}. {category}: {question['question']}**")
                st.caption(
                    f"Based on: {question.get('evidence_or_skill', 'Not specified')}"
                )
                for point in question.get("expected_answer_points", []):
                    st.write(f"- {point}")

    screening = result.get("screening_results") or {}
    if screening.get("summary"):
        st.markdown("### Resume screening observations")
        st.info(screening["summary"])
    report = result.get("final_recruitment_report") or {}
    if report.get("report_text"):
        with st.expander("Final recruitment summary"):
            st.markdown(report["report_text"])
    if result.get("report_pdf_bytes"):
        st.download_button(
            "Download this candidate's PDF report",
            data=result["report_pdf_bytes"],
            file_name=f"{result.get('_session_candidate_id', 'candidate')}_report.pdf",
            mime="application/pdf",
            key=f"download_{result.get('_session_candidate_id', result.get('database_candidate_id'))}",
        )


def _skills_matching() -> None:
    _page_header(
        "Skills matching",
        "Review exact and semantically related resume-backed skills against job requirements.",
    )
    candidate_rows = _records()
    assessment = _candidate_selector(candidate_rows or [])
    if assessment is None:
        return
    details = assessment["candidate_details"]
    st.subheader(details.get("candidate_name") or assessment["resume_file_name"])
    st.caption(
        f"{assessment.get('job_title') or 'Job'}"
        f" · {assessment.get('company_name') or 'Company not specified'}"
    )
    _show_skill_comparison(assessment["skills_comparison"])


def _observation_list(title: str, observations: list[dict[str, Any]]) -> None:
    st.markdown(f"**{title}**")
    if not observations:
        st.write("No observations recorded.")
        return
    for item in observations:
        st.markdown(
            f"- {item.get('observation', 'Observation')}"
            f"\n  - **Evidence:** {item.get('evidence', 'No evidence supplied')}"
        )


def _resume_screening() -> None:
    _page_header(
        "Resume screening",
        "Review evidence-based observations and record your own recruiter decision.",
    )
    candidate_rows = _records()
    assessment = _candidate_selector(candidate_rows or [])
    if assessment is None:
        return
    details = assessment["candidate_details"]
    screening = assessment["screening_results"]
    title = details.get("candidate_name") or assessment["resume_file_name"]
    st.subheader(title)
    contact = " · ".join(
        value for value in (details.get("email"), details.get("phone_number")) if value
    )
    if contact:
        st.caption(contact)
    if details.get("work_experience"):
        st.markdown("**Resume-listed experience**")
        for experience in details["work_experience"]:
            st.write(f"- {experience}")
    _observation_list("Strengths", screening.get("strengths") or [])
    _observation_list("Relevant gaps to discuss", screening.get("relevant_gaps") or [])
    _observation_list(
        "Areas requiring verification",
        screening.get("verification_areas") or [],
    )
    if screening.get("summary"):
        st.info(screening["summary"])
    st.caption("AI observations are decision support only; the recruiter controls the outcome.")

    current_status = assessment.get("reviewer_status", "Under Review")
    selected_status = st.selectbox(
        "Recruiter decision",
        REVIEW_STATUSES,
        index=(
            REVIEW_STATUSES.index(current_status)
            if current_status in REVIEW_STATUSES
            else REVIEW_STATUSES.index("Under Review")
        ),
        key=f"review_status_{assessment['candidate_id']}",
    )
    if st.button("Save recruiter decision", type="primary"):
        local_id = assessment["candidate_id"]
        local_result = next(
            (
                result
                for result in st.session_state.get("analysis_results", [])
                if result.get("_session_candidate_id") == local_id
            ),
            None,
        )
        if local_result is not None:
            local_result["_reviewer_status"] = selected_status
            st.success(
                f"Decision saved for this browser session: {selected_status}"
            )
        else:
            try:
                update_reviewer_status(local_id, selected_status)
                st.success(f"Decision saved: {selected_status}")
            except (
                DatabaseConfigurationError,
                DatabaseOperationError,
                ValueError,
            ) as exc:
                st.error(f"Could not save recruiter decision: {exc}")


def _interview_questions() -> None:
    _page_header(
        "Interview questions",
        "Explore candidate-specific technical and project questions by difficulty.",
    )
    candidate_rows = _records()
    assessment = _candidate_selector(candidate_rows or [])
    if assessment is None:
        return
    details = assessment["candidate_details"]
    st.subheader(details.get("candidate_name") or assessment["resume_file_name"])
    questions = assessment["interview_questions"]
    for difficulty in ("beginner", "intermediate", "advanced"):
        with st.expander(difficulty.title(), expanded=difficulty == "beginner"):
            grouped = [
                question
                for question in questions
                if question.get("difficulty") == difficulty
            ]
            if not grouped:
                st.write("No questions at this difficulty were generated.")
            for index, question in enumerate(grouped, start=1):
                category = question.get("category", "technical").title()
                st.markdown(f"**{index}. {category}: {question['question']}**")
                st.caption(
                    f"Targets: {question.get('evidence_or_skill', 'Not specified')}"
                )
                st.markdown("Expected answer points:")
                for point in question.get("expected_answer_points", []):
                    st.write(f"- {point}")


def _candidate_reports() -> None:
    _page_header(
        "Candidate reports",
        "View the complete AI-generated assessment and download its PDF.",
    )
    candidate_rows = _records()
    assessment = _candidate_selector(candidate_rows or [])
    if assessment is None:
        return
    details = assessment["candidate_details"]
    st.subheader(details.get("candidate_name") or assessment["resume_file_name"])
    st.json(
        {
            "Candidate": details,
            "Job": {
                "title": assessment.get("job_title"),
                "company": assessment.get("company_name"),
            },
            "Reviewer status": assessment.get("reviewer_status"),
        },
        expanded=False,
    )
    st.markdown("### Skills matching")
    _show_skill_comparison(assessment["skills_comparison"])
    st.markdown("### Screening observations")
    screening = assessment["screening_results"]
    _observation_list("Strengths", screening.get("strengths") or [])
    _observation_list("Relevant gaps", screening.get("relevant_gaps") or [])
    _observation_list(
        "Verification areas", screening.get("verification_areas") or []
    )
    st.markdown("### Interview questions")
    for question in assessment["interview_questions"]:
        st.markdown(
            f"- **{question.get('difficulty', '').title()} · "
            f"{question.get('category', '').title()}:** {question.get('question')}"
        )
    report_text = assessment.get("report", {}).get("report_text") or ""
    st.markdown("### Final recruitment summary")
    if report_text:
        st.markdown(report_text)
    else:
        st.info("No final recruitment summary is stored for this record.")

    pdf_bytes = assessment.get("pdf_bytes")
    pdf_path = assessment.get("pdf_path")
    if pdf_bytes is None and pdf_path:
        try:
            saved_path = Path(pdf_path)
            if saved_path.is_file():
                pdf_bytes = saved_path.read_bytes()
        except OSError as exc:
            st.warning(f"Could not read the saved PDF; regenerating it: {exc}")
    if pdf_bytes is None and report_text:
        try:
            pdf_bytes = create_pdf_report(report_text)
        except ReportAgentError as exc:
            st.error(f"Could not prepare the PDF download: {exc}")
    if pdf_bytes:
        filename = (
            f"{assessment.get('candidate_id', 'candidate')}_recruitment_report.pdf"
        )
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            type="primary",
        )


def main() -> None:
    with st.sidebar:
        st.markdown('<div class="brand">TalentDesk</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="brand-subtitle">AI recruitment workspace</div>',
            unsafe_allow_html=True,
        )
        page = st.selectbox(
            "Workspace",
            PAGES,
            index=PAGES.index("Resume Upload"),
            key="navigation",
        )
        st.divider()
        st.caption("AI-generated outputs are decision support for human reviewers.")

    renderers = {
        "Dashboard": _dashboard,
        "Job Management": _job_management,
        "Resume Upload": _resume_upload,
        "Skills Matching": _skills_matching,
        "Resume Screening": _resume_screening,
        "Interview Questions": _interview_questions,
        "Candidate Reports": _candidate_reports,
    }
    renderers[page]()


if __name__ == "__main__":
    main()
