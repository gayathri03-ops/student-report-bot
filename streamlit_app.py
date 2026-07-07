import json
from pathlib import Path
 
import pandas as pd
import requests
import streamlit as st
 
BACKEND_URL = "http://127.0.0.1:8000/query"
HISTORY_URL = "http://127.0.0.1:8000/history"
SAVED_PROMPTS_FILE = Path(__file__).parent / "data" / "saved_prompts.json"
 
st.set_page_config(page_title="Student Result Query Bot", page_icon="🎓")
st.title("🎓 Student Result Query Bot")
st.caption("Ask about marks, attendance, or class performance.")
 
 
def call_bot(question: str, user_role: str, own_reg_no: str | None) -> dict:
    payload = {"question": question, "role": user_role, "own_reg_no": own_reg_no}
    try:
        resp = requests.post(BACKEND_URL, json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Backend not running -> fall back to direct in-process call.
        from app.bot import answer_question
        return answer_question(question, role=user_role, own_reg_no=own_reg_no)
 
 
def fetch_history(limit: int = 10) -> list:
    try:
        resp = requests.get(HISTORY_URL, params={"limit": limit}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        from app import logging_store
        return logging_store.read_recent_interactions(limit=limit)
 
 
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
 
 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
 
# --- Sidebar: role selector, saved questions, reset, history --------------
with st.sidebar:
    st.subheader("👤 Access Role")
    user_role = st.radio("I am a:", ["Student", "Admin"], horizontal=True)
    user_role = user_role.lower()
 
    own_reg_no = None
    if user_role == "student":
        own_reg_no = st.text_input("Your register number", placeholder="e.g. 411723106003")
        st.caption("As a student, you can only view your own result/attendance "
                     "and class-wide aggregates -- not other students' names.")
    else:
        st.caption("Admin can view all data, including rankings and failed-student lists.")
 
    st.divider()
    st.subheader("💾 Saved Questions")
    for p in load_saved_prompts():
        if st.button(p, key=f"saved_{p}", use_container_width=True):
            st.session_state.pending_question = p
 
    st.divider()
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
 
    with st.expander("🕘 Recent Interaction Log"):
        for entry in reversed(fetch_history(limit=10)):
            st.caption(f"[{entry['timestamp'][:19]}] ({entry['role']}) {entry['question']}")
 
# --- Main chat area ---------------------------------------------------------
for msg in st.session_state.chat_history:
    with st.chat_message(msg["speaker"]):
        st.markdown(msg["content"])
 
pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("Ask about a result, attendance, or class performance...")
question = pending or user_input
 
if question:
    if user_role == "student" and not own_reg_no:
        st.warning("Please enter your register number in the sidebar first.")
    else:
        st.session_state.chat_history.append({"speaker": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
 
        result = call_bot(question, user_role, own_reg_no)
 
        with st.chat_message("assistant"):
            st.markdown(result["answer"])
 
            # Chart output: show a bar chart when we have per-subject marks
            # (single student result) or a class-wide numeric breakdown.
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
                if st.button("Save", key=f"save_{len(st.session_state.chat_history)}"):
                    save_prompt(question)
                    st.toast("Saved!")
 
        st.session_state.chat_history.append({"speaker": "assistant", "content": result["answer"]})
 