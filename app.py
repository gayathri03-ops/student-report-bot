import streamlit as st
from queries import *

st.title("🎓 Student Result Query Bot")

question = st.text_input("Ask your question:")

if question:
    if "all students" in question.lower():
        st.write(get_all_students())

    elif "marks of" in question.lower():
        name = question.split("marks of")[-1].strip().capitalize()
        st.write(get_student_marks(name))

    elif "high scorers" in question.lower():
        st.write(get_high_scorers())

    else:
        st.write("Sorry, I don't understand the question.")