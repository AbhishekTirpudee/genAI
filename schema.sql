CREATE TABLE IF NOT EXISTS jobs (
    job_id CHAR(64) PRIMARY KEY,
    job_description LONGTEXT NOT NULL,
    job_title VARCHAR(255) NULL,
    company_name VARCHAR(255) NULL,
    required_skills JSON NULL,
    experience_requirements TEXT NULL,
    job_location VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candidates (
    candidate_id CHAR(36) PRIMARY KEY,
    job_id CHAR(64) NOT NULL,
    resume_file_name VARCHAR(255) NOT NULL,
    candidate_name VARCHAR(255) NULL,
    email VARCHAR(320) NULL,
    phone_number VARCHAR(64) NULL,
    candidate_details JSON NOT NULL,
    reviewer_status VARCHAR(32) NOT NULL DEFAULT 'Under Review',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_candidates_email (email),
    CONSTRAINT fk_candidates_job
        FOREIGN KEY (job_id) REFERENCES jobs (job_id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS skill_matches (
    candidate_id CHAR(36) PRIMARY KEY,
    required_skills JSON NOT NULL,
    candidate_skills JSON NOT NULL,
    exact_matches JSON NOT NULL,
    related_matches JSON NOT NULL,
    missing_skills JSON NOT NULL,
    matching_percentage DECIMAL(5, 1) NULL,
    score_calculation TEXT NOT NULL,
    short_explanation TEXT NULL,
    CONSTRAINT fk_skill_matches_candidate
        FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS screening_reports (
    candidate_id CHAR(36) PRIMARY KEY,
    strengths JSON NOT NULL,
    relevant_gaps JSON NOT NULL,
    verification_areas JSON NOT NULL,
    summary TEXT NOT NULL,
    CONSTRAINT fk_screening_candidate
        FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interview_questions (
    candidate_id CHAR(36) PRIMARY KEY,
    questions JSON NOT NULL,
    CONSTRAINT fk_interview_candidate
        FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recruitment_reports (
    candidate_id CHAR(36) PRIMARY KEY,
    report_text LONGTEXT NOT NULL,
    pdf_path VARCHAR(1024) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_report_candidate
        FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;
