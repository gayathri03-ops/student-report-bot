import os
import sqlite3
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()

def generate_sql(question):
    prompt = f"""
    Convert the following question into SQL query.
    Database name: students.db
    Table name: students
    Columns: id, name, marks, attendance, department, grade
    Rules:
    - Return only the raw SQL query text
    - Do not add any text or explanation
    - Do not use markdown backticks like ```sql
    - Use only the students table
    - Use only available columns
    Question: {question}
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # FIXED: Added [0] here
    sql = response.choices[0].message.content.strip()
    
    lines = [line.strip() for line in sql.split("\n") if line.strip()]
    cleaned_lines = [line for line in lines if not line.startswith("```")]
    sql = " ".join(cleaned_lines)
    sql = sql.replace("`", "").strip()
    
    if sql.endswith(";"):
        sql = sql[:-1].strip()
        
    return sql

def run_query(sql):
    try:
        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        columns = [desc for desc in cursor.description]
        conn.close()
        return result, columns
    except Exception as e:
        return f"Error: {e}", None

def explain_result(question, result_data):
    prompt = f"""
    Explain these database results in one or two clear sentences to answer the user's question.
    User Question: {question}
    Database Rows: {result_data}
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    # FIXED: Added [0] here
    return response.choices[0].message.content.strip()
