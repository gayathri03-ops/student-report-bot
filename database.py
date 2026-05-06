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
    (2, "Arun", 78, 85),
    (3, "Priya", 92, 95),
    (4, "Karthik", 70, 80),
    (5, "Meena", 88, 92)
]

cursor.executemany(
    "INSERT OR IGNORE INTO students (id, name, marks, attendance) VALUES (?, ?, ?, ?)",
    students_data
)

print("Sample data inserted!")
conn.commit()
conn.close()