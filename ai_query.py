import sqlite3
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

import os
import sqlite3
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(question):
    prompt = f"""
You are an SQL expert.

Table: students(id, name, marks, attendance)

Rules:
- Only return SQL query
- Do not explain anything
- No markdown, no ``` symbols

Question: {question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql

def run_query(sql):
    try:
        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute(sql)
        result = cursor.fetchall()

        conn.close()

        if result and len(result[0]) == 1:
            result = [row[0] for row in result]

        if isinstance(result, list) and len(result) == 1:
            return result[0]

        return result

    except Exception as e:
        return f"Error: {e}"