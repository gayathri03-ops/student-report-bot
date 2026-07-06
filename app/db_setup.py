"""
db_setup.py
-----------
Builds a SQLite database from the raw students.csv dataset.

This is the "knowledge base" for the bot: a clean, schema-known table
that the safe query layer (safe_query.py) is allowed to read from.

Run this once (or whenever the CSV changes) via:
    python -m app.db_setup
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "students.csv"
DB_PATH = BASE_DIR / "data" / "students.db"

PASS_MARK = 50  # marks required per subject to pass


def build_database(csv_path: Path = CSV_PATH, db_path: Path = DB_PATH) -> None:
    df = pd.read_csv(csv_path)

    subject_marks_cols = [c for c in df.columns if c.endswith("_marks")]

    df["total_marks"] = df[subject_marks_cols].sum(axis=1)
    df["max_marks"] = len(subject_marks_cols) * 100
    df["percentage"] = (df["total_marks"] / df["max_marks"] * 100).round(2)
    df["subjects_failed"] = df[subject_marks_cols].apply(
        lambda row: sum(1 for m in row if m < PASS_MARK), axis=1
    )
    df["result_status"] = df["subjects_failed"].apply(
        lambda failed: "PASS" if failed == 0 else "FAIL"
    )

    conn = sqlite3.connect(db_path)
    df.to_sql("students", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Database built at {db_path} with {len(df)} student records.")


if __name__ == "__main__":
    build_database()
