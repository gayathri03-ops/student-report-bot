import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_sql(question):
    prompt = f"""
    You are an SQL expert.

    Table: students(id, name, marks, attendance)

    Convert this question into SQL query:
    {question}

    Only return SQL query.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def run_query(sql_query):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    try:
        cursor.execute(sql_query)
        result = cursor.fetchall()
    except Exception as e:
        result = str(e)

    conn.close()
    return result