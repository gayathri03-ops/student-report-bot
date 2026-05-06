import sqlite3

def get_all_students():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    conn.close()
    return data


def get_student_marks(name):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT marks FROM students WHERE name=?", (name,))
    data = cursor.fetchone()

    conn.close()
    return data


def get_high_scorers():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE marks > 80")
    data = cursor.fetchall()

    conn.close()
    return data