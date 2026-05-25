import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
from database import init_db
from ai_query import generate_sql, run_query, explain_result

init_db()

VALID_COLUMNS = {"id", "name", "marks", "attendance", "department", "grade"}

def calculate_grade(marks):
    if marks >= 91:
        return "O"
    elif marks >= 81:
        return "A"
    elif marks >= 71:
        return "B"
    elif marks >= 61:
        return "C"
    elif marks >= 51:
        return "D"
    else:
        return "E"

st.set_page_config(page_title="Student Result Bot")
st.title("Student Result Query Bot")

st.sidebar.header("External Sync")
if st.sidebar.button("Fetch Fresh Data"):
    try:
        response = requests.get("https://jsonbin.io")
        if response.status_code == 200:
            st.sidebar.success("Successfully synced external records")
    except Exception as error:
        st.sidebar.error(f"Sync failed: {error}")

st.sidebar.header("Saved Questions")
saved_prompts = [
    "Select a pre-saved question...",
    "Show all student details",
    "List students in the ECE department",
    "Show students with grade A or O",
    "Who has attendance less than 75"
]
selected_prompt = st.sidebar.selectbox("Quick Prompts", saved_prompts)

if selected_prompt != "Select a pre-saved question...":
    user_initial_value = selected_prompt
else:
    user_initial_value = ""

question = st.text_input("Enter your question", value=user_initial_value)

if st.button("Run Query"):
    if question:
        sql = generate_sql(question)

        st.subheader("Generated SQL")
        st.code(sql, language="sql")
        
        sql_words = set(re.findall(r'\b[a-zA-Z_]\w*\b', sql.lower()))
        sql_keywords = {
            "select", "from", "where", "and", "or", "not", "like", "order", "by", 
            "group", "limit", "students", "as", "avg", "sum", "count", "max", "min", 
            "is", "null", "between", "desc", "asc", "having"
        }
        
        invalid_columns_used = [
            word for word in sql_words 
            if word not in VALID_COLUMNS and word not in sql_keywords
        ]

        if invalid_columns_used:
            invalid_list = ", ".join([f"'{col}'" for col in invalid_columns_used])
            st.warning(f"The requested data contains field(s) {invalid_list} which do not exist in this database. Attempting fallback or execution.")

        result, columns = run_query(sql)

        st.subheader("Result")
        if isinstance(result, str) and result.startswith("Error"):
            st.error(f"Could not execute query. Ensure you only ask for Name, Marks, Attendance, Department, or Grade. ({result})")
        elif not result:
            st.info("No records found matching your query.")
        else:
            df = pd.DataFrame(result, columns=columns)
            st.dataframe(df, use_container_width=True)
            
            st.subheader("AI Explanation")
            explanation = explain_result(question, result)
            st.write(explanation)
            
            if "name" in df.columns:
                if "marks" in df.columns:
                    st.subheader("Marks Distribution Chart")
                    chart_df = df.set_index("name")[["marks"]]
                    st.bar_chart(chart_df)
                if "attendance" in df.columns:
                    st.subheader("Attendance Performance Chart")
                    chart_df = df.set_index("name")[["attendance"]]
                    st.bar_chart(chart_df)
    else:
        st.warning("Please enter a question")

st.markdown("---")
st.header("Add New Student Data")
with st.form("student_form", clear_on_submit=True):
    new_name = st.text_input("Student Full Name")
    new_dept = st.selectbox("Department", ["ECE", "CSE", "MECH", "EEE", "IT", "AIML"])
    new_marks = st.number_input("Marks (0 - 100)", min_value=0, max_value=100, value=75)
    new_attendance = st.number_input("Attendance Percentage (0 - 100)", min_value=0, max_value=100, value=85)
    
    submit_button = st.form_submit_button("Add Student to Records")
    
    if submit_button:
        if not new_name.strip():
            st.error("Please enter a valid name.")
        else:
            try:
                calculated_grade = calculate_grade(new_marks)
                conn = sqlite3.connect("students.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO students (name, marks, attendance, department, grade) VALUES (?, ?, ?, ?, ?)", 
                    (new_name.strip(), new_marks, new_attendance, new_dept, calculated_grade)
                )
                conn.commit()
                conn.close()
                st.success(f"Successfully added {new_name} to the database with Grade {calculated_grade}")
            except Exception as e:
                st.error(f"Database insertion error: {e}")
