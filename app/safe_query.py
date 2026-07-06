"""
safe_query.py
-------------
The "safe query execution" layer.

Rule: the bot NEVER lets an LLM write raw SQL and execute it directly.
Instead, the NLU layer (nlu.py) only ever picks one of these whitelisted,
parameterized functions. Every query here uses '?' placeholders (never
string-formatted SQL), and only SELECTs against the known schema.
"""

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "students.db"

SUBJECT_COLUMNS = {
    1: ("subject1_name", "subject1_marks"),
    2: ("subject2_name", "subject2_marks"),
    3: ("subject3_name", "subject3_marks"),
    4: ("subject4_name", "subject4_marks"),
    5: ("subject5_name", "subject5_marks"),
}


def _connect():
    return sqlite3.connect(DB_PATH)


def get_student_result(reg_no: str) -> Optional[dict]:
    """Full result card for one student, by register number."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cur = conn.execute("SELECT * FROM students WHERE reg_no = ?", (reg_no,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_attendance(reg_no: str) -> Optional[dict]:
    """Attendance percentage for one student."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT reg_no, name, attendance_percent FROM students WHERE reg_no = ?",
        (reg_no,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_class_average(subject_col: str) -> Optional[float]:
    """Class average for one subject's marks column. subject_col must be whitelisted."""
    valid_cols = {v[1] for v in SUBJECT_COLUMNS.values()}
    if subject_col not in valid_cols:
        raise ValueError(f"Unknown/unauthorized subject column: {subject_col}")
    conn = _connect()
    cur = conn.execute(f"SELECT AVG({subject_col}) FROM students")  # nosec: subject_col whitelisted above
    avg = cur.fetchone()[0]
    conn.close()
    return round(avg, 2) if avg is not None else None

def get_class_average_overall() -> Optional[float]:
    conn = _connect()
    cur = conn.execute("SELECT AVG(percentage) FROM students")
    avg = cur.fetchone()[0]
    conn.close()
    return round(avg, 2) if avg is not None else None


def get_top_performers(n: int = 5) -> list:
    n = max(1, min(int(n), 50))  # clamp to a sane, safe range
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT reg_no, name, total_marks, percentage FROM students "
        "ORDER BY percentage DESC LIMIT ?",
        (n,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_failed_students() -> list:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT reg_no, name, subjects_failed, percentage FROM students "
        "WHERE result_status = 'FAIL' ORDER BY subjects_failed DESC"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_class_performance_summary() -> dict:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    total = conn.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]
    passed = conn.execute(
        "SELECT COUNT(*) AS c FROM students WHERE result_status='PASS'"
    ).fetchone()["c"]
    avg_pct = conn.execute("SELECT AVG(percentage) AS a FROM students").fetchone()["a"]
    avg_att = conn.execute(
        "SELECT AVG(attendance_percent) AS a FROM students"
    ).fetchone()["a"]
    conn.close()
    return {
        "total_students": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_percent": round(passed / total * 100, 2) if total else 0,
        "class_average_percentage": round(avg_pct, 2) if avg_pct else 0,
        "class_average_attendance": round(avg_att, 2) if avg_att else 0,
    }
