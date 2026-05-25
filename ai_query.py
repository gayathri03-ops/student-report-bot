import os
import sqlite3
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(question):

    prompt = f"""
    Convert the following question into SQL query.

    Database name: students.db
    Table name: students

    Columns:
    id
    name
    marks
    attendance

    Rules:
    - Return only SQL query
    - Do not add explanation
    - Do not use markdown
    - Use only the students table
    - Use only available columns

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    sql = response.choices[0].message.content.strip()

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

        return result

    except Exception as e:
        return f"Error: {e}"