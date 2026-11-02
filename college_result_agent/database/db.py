"""
Database helper and query execution engine for College Result Analysis System.
"""

import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), 'college_results.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def execute_safe_query(sql, params=None):
    """
    Executes a read-only SQL query safely.
    Returns:
      dict with:
        'success': bool,
        'columns': list of column names,
        'rows': list of dicts/tuples,
        'row_count': int,
        'execution_time_ms': float,
        'error': str or None
    """
    start_time = time.perf_counter()
    params = params or ()
    
    # Defense in depth: Check for destructive keywords
    stripped = sql.strip().upper()
    destructive_keywords = [
        'DROP ', 'DELETE ', 'UPDATE ', 'INSERT ', 'ALTER ', 'TRUNCATE ',
        'CREATE ', 'REPLACE ', 'ATTACH ', 'DETACH ', 'PRAGMA ', 'VACUUM '
    ]
    for kw in destructive_keywords:
        if stripped.startswith(kw) or f";{kw}" in stripped.replace(" ", ""):
            return {
                'success': False,
                'columns': [],
                'rows': [],
                'row_count': 0,
                'execution_time_ms': 0,
                'error': f"Query rejected: Only read-only SELECT queries are permitted. Detected forbidden operation '{kw.strip()}'."
            }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows_raw = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(row) for row in rows_raw]
        conn.close()
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            'success': True,
            'columns': columns,
            'rows': rows,
            'row_count': len(rows),
            'execution_time_ms': elapsed_ms,
            'error': None
        }
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            'success': False,
            'columns': [],
            'rows': [],
            'row_count': 0,
            'execution_time_ms': elapsed_ms,
            'error': str(e)
        }

def get_schema_summary():
    """Returns structured table and view schema definitions for the Agent and UI."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables and views
    cursor.execute("""
        SELECT type, name FROM sqlite_master 
        WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
    """)
    entities = cursor.fetchall()
    
    schema_info = {}
    for entity_type, name in entities:
        cursor.execute(f"PRAGMA table_info({name})")
        cols = cursor.fetchall()
        schema_info[name] = {
            'type': entity_type,
            'columns': [{'name': col['name'], 'type': col['type'], 'pk': bool(col['pk'])} for col in cols]
        }
    conn.close()
    return schema_info
