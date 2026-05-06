import sqlite3

# connect to database (creates file if not exists)
conn = sqlite3.connect("students.db")

cursor = conn.cursor()

# create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    name TEXT,
    marks INTEGER,
    attendance INTEGER
)
""")

print("Database created successfully!")

# insert sample data
students_data = [
    (1, "Gayathri", 85, 90),
    (2, "Ashok", 78, 85),
    (3, "Prashika", 92, 95),
    (4, "Karthikesh", 70, 80),
    (5, "Dineshkumar", 88, 92),
    (6, "Mabhu", 70,60)
]

cursor.executemany(
    "INSERT OR IGNORE INTO students (id, name, marks, attendance) VALUES (?, ?, ?, ?)",
    students_data
)

print("Sample data inserted!")
conn.commit()
conn.close()