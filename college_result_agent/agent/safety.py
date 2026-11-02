"""
SQL Safety and Validation Module.
Prevents destructive queries, SQL injection risks, and restricts operations to read-only queries.
"""

import re

ALLOWED_READ_KEYWORDS = ('SELECT', 'WITH')
DISALLOWED_KEYWORDS = [
    r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', r'\bALTER\b',
    r'\bTRUNCATE\b', r'\bCREATE\b', r'\bREPLACE\b', r'\bATTACH\b', r'\bDETACH\b',
    r'\bPRAGMA\b', r'\bVACUUM\b', r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b'
]

def sanitize_and_validate_sql(sql: str) -> tuple[bool, str, str]:
    """
    Validates and sanitizes a SQL query string.
    Returns:
        (is_valid: bool, sanitized_sql: str, error_message: str)
    """
    if not sql or not sql.strip():
        return False, "", "Empty SQL query provided."
    
    clean_sql = sql.strip().rstrip(';')
    
    # Check for forbidden keywords using regex word boundary
    for pattern in DISALLOWED_KEYWORDS:
        if re.search(pattern, clean_sql, re.IGNORECASE):
            match = re.search(pattern, clean_sql, re.IGNORECASE).group()
            return False, "", f"Operation '{match.upper()}' is forbidden. Only analytical SELECT queries are permitted."

    # Must start with SELECT or WITH
    upper_sql = clean_sql.upper().strip()
    if not any(upper_sql.startswith(kw) for kw in ALLOWED_READ_KEYWORDS):
        return False, "", "Queries must begin with SELECT or WITH."

    # Prevent chained queries with semicolon
    if ';' in clean_sql:
        parts = [p.strip() for p in clean_sql.split(';') if p.strip()]
        if len(parts) > 1:
            return False, "", "Multi-statement queries separated by ';' are not allowed."
        clean_sql = parts[0]

    return True, clean_sql, ""
