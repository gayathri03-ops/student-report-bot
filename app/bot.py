"""
bot.py
------
The orchestrator: question -> NLU (intent) -> safe_query (data) -> explain (text).
This is the single function both the FastAPI backend and the Streamlit UI call.
 
Week 2 addition: when the question doesn't match one of the fixed intents,
we fall back to the retrieval layer (retrieval.py) to find the most relevant
student record(s), then still fetch the actual facts through safe_query.py
(never straight from the retrieved text) and attach a citation showing which
record(s) the answer is based on and how confident the match is.
"""
 
from app import nlu, safe_query, explain, retrieval
 
# Below this similarity score, we don't trust the retrieval match enough
# to answer from it -- we say we don't know rather than guess.
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.15
 
 
def answer_question(question: str) -> dict:
    parsed = nlu.parse_question(question)
    data = None
    answer = ""
 
    needs_retrieval_fallback = False
 
    if parsed.intent == "get_result":
        if not parsed.reg_no:
            needs_retrieval_fallback = True
        else:
            data = safe_query.get_student_result(parsed.reg_no)
            answer = explain.explain_result(data) if data else (
                f"No student found with register number {parsed.reg_no}."
            )
 
    elif parsed.intent == "get_attendance":
        if not parsed.reg_no:
            needs_retrieval_fallback = True
        else:
            data = safe_query.get_attendance(parsed.reg_no)
            answer = explain.explain_attendance(data) if data else (
                f"No student found with register number {parsed.reg_no}."
            )
 
    elif parsed.intent == "get_class_average":
        if parsed.subject_col:
            avg = safe_query.get_class_average(parsed.subject_col)
            data = {"subject_col": parsed.subject_col, "average": avg}
            answer = explain.explain_class_average(parsed.subject_col, avg)
        else:
            avg = safe_query.get_class_average_overall()
            data = {"average": avg}
            answer = f"The overall class average is {avg}%."
 
    elif parsed.intent == "get_top_performers":
        data = safe_query.get_top_performers(parsed.top_n)
        answer = explain.explain_top_performers(data)
 
    elif parsed.intent == "get_failed_students":
        data = safe_query.get_failed_students()
        answer = explain.explain_failed_students(data)
 
    elif parsed.intent == "get_class_summary":
        data = safe_query.get_class_performance_summary()
        answer = explain.explain_class_summary(data)
 
    elif parsed.intent == "unknown":
        needs_retrieval_fallback = True
 
    if needs_retrieval_fallback:
        # Fall back to retrieval: find the most relevant student record(s)
        # for this freeform question, then re-fetch facts safely (never
        # trust numbers straight out of the retrieved text).
        matches = retrieval.retrieve(question, k=1)
        if matches and matches[0]["score"] >= RETRIEVAL_CONFIDENCE_THRESHOLD:
            best = matches[0]
            record = safe_query.get_student_result(best["reg_no"])
            if record:
                data = record
                citation = f"[matched record: {record['reg_no']} - {record['name']}, confidence {best['score']}]"
                answer = explain.explain_result(record) + f"\n\n{citation}"
                parsed.intent = "retrieve_context"
            else:
                answer = (
                    "I couldn't confidently match that question to a student "
                    "record. Try including a register number, or ask about "
                    "results, attendance, top performers, failed students, "
                    "or the class summary."
                )
        else:
            answer = (
                "I can help with: your result (give your register number), "
                "attendance, class averages, top performers, failed students, "
                "or an overall class summary. Try asking something like "
                "'What is my result for 411723106003?'"
            )
 
    answer = explain.maybe_llm_polish(answer, question)
    return {"intent": parsed.intent, "answer": answer, "data": data}
 