import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            marks INTEGER NOT NULL,
            attendance INTEGER NOT NULL,
            department TEXT NOT NULL,
            grade TEXT NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        try:
            external_source_url = "https://githubusercontent.com"
            df = pd.read_csv(external_source_url)
            df.to_sql("students", conn, if_exists="append", index=False)
        except Exception:
            sample_data = [
                ("Gayathri", 85, 92, "ECE", "A"),
                ("Ashok", 78, 80, "CSE", "B"),
                ("Prashika", 92, 95, "ECE", "O"),
                ("Karthikesh", 65, 74, "MECH", "C"),
                ("Dineshkumar", 55, 72, "CSE", "D"),
                ("Mabhu", 89, 68, "AIML", "A"),
                ("Saniya Mirza", 62, 95, "MECH", "E")     
            ]
            cursor.executemany("INSERT INTO students (name, marks, attendance, department, grade) VALUES (?, ?, ?, ?, ?)", sample_data)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
