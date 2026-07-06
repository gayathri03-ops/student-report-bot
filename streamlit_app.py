"""
streamlit_app.py
-----------------
Basic chat interface for the Student Result Query Bot (Week 1 deliverable),
extended with saved prompts and chart output (Week 3 features get layered
on top of this same file as the project progresses).

Run with:
    streamlit run streamlit_app.py

It calls the FastAPI backend if running (recommended, matches the
FastAPI + Streamlit stack); otherwise it falls back to calling the bot
logic directly in-process so the UI still works stand-alone.
"""

import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = "http://127.0.0.1:8000/query"
SAVED_PROMPTS_FILE = Path(__file__).parent / "data" / "saved_prompts.json"

st.set_page_config(page_title="Student Result Query Bot", page_icon="🎓")
st.title("🎓 Student Result Query Bot")
st.caption("Ask about marks, attendance, or class performance.")


def call_bot(question: str) -> dict:
    try:
        resp = requests.post(BACKEND_URL, json={"question": question}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Backend not running -> fall back to direct in-process call.
        from app.bot import answer_question
        return answer_question(question)


def load_saved_prompts() -> list:
    if SAVED_PROMPTS_FILE.exists():
        return json.loads(SAVED_PROMPTS_FILE.read_text())
    return [
        "What is my result for 411723106003?",
        "What is my attendance for 411723106004?",
        "Who are the top 5 performers?",
        "List all failed students",
        "Give me the class performance summary",
    ]


def save_prompt(prompt: str) -> None:
    prompts = load_saved_prompts()
    if prompt not in prompts:
        prompts.append(prompt)
        SAVED_PROMPTS_FILE.parent.mkdir(exist_ok=True)
        SAVED_PROMPTS_FILE.write_text(json.dumps(prompts, indent=2))


if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Saved Questions")
    for p in load_saved_prompts():
        if st.button(p, key=f"saved_{p}", use_container_width=True):
            st.session_state.pending_question = p

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Ask about a result, attendance, or class performance...")
question = pending or user_input

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    result = call_bot(question)

    with st.chat_message("assistant"):
        st.markdown(result["answer"])

        # Chart output feature: show a bar chart when we have per-subject
        # marks (single student result) or a class-wide numeric breakdown.
        data = result.get("data")
        if isinstance(data, dict) and "subject1_marks" in data:
            chart_df = pd.DataFrame({
                "Subject": [data[f"subject{i}_name"] for i in range(1, 6)],
                "Marks": [data[f"subject{i}_marks"] for i in range(1, 6)],
            }).set_index("Subject")
            st.bar_chart(chart_df)
        elif isinstance(data, list) and data and "percentage" in data[0]:
            chart_df = pd.DataFrame(data).set_index("name")[["percentage"]]
            st.bar_chart(chart_df)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save", key=f"save_{len(st.session_state.history)}"):
                save_prompt(question)
                st.toast("Saved!")

    st.session_state.history.append({"role": "assistant", "content": result["answer"]})