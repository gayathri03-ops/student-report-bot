import streamlit as st
from ai_query import generate_sql, run_query

st.set_page_config(page_title="Student Result Bot")

st.title("Student Result Query Bot")

st.write("Ask any student-related question")

question = st.text_input("Enter your question")

if st.button("Run Query"):

    if question:

        sql = generate_sql(question)

        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        result = run_query(sql)

        st.subheader("Result")
        st.write(result)

    else:
        st.warning("Please enter a question")