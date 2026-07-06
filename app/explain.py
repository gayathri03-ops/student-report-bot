"""
explain.py
----------
"Result explanation" feature: turns structured query results into a
natural-language answer. Template-based by default (reliable, free,
explainable in viva); optionally rephrased by an LLM if OPENAI_API_KEY
is set, purely for wording -- the facts always come from safe_query.py,
never from the LLM.
"""
 
import os
from typing import Optional
 
SUBJECT_COL_TO_LABEL = {
    "subject1_marks": "Circuit Theory",
    "subject2_marks": "Digital Electronics",
    "subject3_marks": "Signals and Systems",
    "subject4_marks": "Data Structures",
    "subject5_marks": "Engineering Maths",
}
 
 
def explain_result(record: dict) -> str:
    subjects = []
    for i in range(1, 6):
        name = record.get(f"subject{i}_name")
        marks = record.get(f"subject{i}_marks")
        if name is not None:
            subjects.append(f"{name}: {marks}")
    subject_lines = "\n".join(f"  - {s}" for s in subjects)
    return (
        f"Result for {record['name']} ({record['reg_no']}):\n"
        f"{subject_lines}\n"
        f"  Total: {record['total_marks']}/{record['max_marks']} "
        f"({record['percentage']}%)\n"
        f"  Status: {record['result_status']}"
        + (f" ({record['subjects_failed']} subject(s) below pass mark)"
           if record["result_status"] == "FAIL" else "")
    )
 
 
def explain_attendance(record: dict) -> str:
    pct = record["attendance_percent"]
    note = " (below the 75% minimum)" if pct < 75 else ""
    return f"{record['name']} ({record['reg_no']}) has {pct}% attendance{note}."
 
 
def explain_class_average(subject_col: str, avg: Optional[float]) -> str:
    label = SUBJECT_COL_TO_LABEL.get(subject_col, subject_col)
    if avg is None:
        return f"No data available to compute the class average for {label}."
    return f"The class average for {label} is {avg}%."
 
 
def explain_top_performers(rows: list) -> str:
    if not rows:
        return "No student records found."
    lines = [
        f"{i+1}. {r['name']} ({r['reg_no']}) - {r['percentage']}%"
        for i, r in enumerate(rows)
    ]
    return "Top performers:\n" + "\n".join(lines)
 
 
def explain_failed_students(rows: list) -> str:
    if not rows:
        return "No students have failed - everyone has passed all subjects."
    lines = [
        f"- {r['name']} ({r['reg_no']}): {r['subjects_failed']} subject(s) failed, "
        f"{r['percentage']}% overall"
        for r in rows
    ]
    return "Students with failing subjects:\n" + "\n".join(lines)
 
 
def explain_class_summary(summary: dict) -> str:
    return (
        f"Class Performance Summary:\n"
        f"  Total students: {summary['total_students']}\n"
        f"  Passed: {summary['passed']} | Failed: {summary['failed']}\n"
        f"  Pass rate: {summary['pass_rate_percent']}%\n"
        f"  Class average marks: {summary['class_average_percentage']}%\n"
        f"  Class average attendance: {summary['class_average_attendance']}%"
    )
 
 
def maybe_llm_polish(plain_text: str, original_question: str) -> str:
    """Optionally rephrase the factual answer more conversationally via LLM.
    Facts are never altered - only wording. Falls back silently to plain_text.
 
    Week 2 prompt tuning notes:
    - The system prompt explicitly separates "citation" lines (in brackets)
      from the main answer and instructs the model to preserve them verbatim,
      since these carry which record/confidence the answer is grounded in.
    - temperature=0 (down from 0.2) for more consistent, less "creative"
      wording -- we don't want the rephrasing to introduce ambiguity.
    - Explicit output-length constraint keeps answers demo/viva-friendly.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return plain_text
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
 
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You rephrase a factual answer for a student-facing chatbot. "
             "Rules:\n"
             "1. Do NOT change, add, invent, or remove any numbers, names, "
             "or facts -- copy them exactly as given.\n"
             "2. If the answer contains a line wrapped in square brackets "
             "like '[matched record: ...]', treat it as a citation: keep "
             "it verbatim, on its own line, at the end.\n"
             "3. Keep the response under 4 sentences (excluding any list "
             "of names/marks that must stay itemized).\n"
             "4. Friendly, plain tone -- no filler, no repeating the question."),
            ("user", "Question: {question}\n\nFactual answer:\n{answer}"),
        ])
        chain = prompt | llm
        response = chain.invoke({"question": original_question, "answer": plain_text})
        return response.content.strip()
    except Exception:
        return plain_text
 