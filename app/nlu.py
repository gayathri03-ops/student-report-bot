"""
nlu.py
------
Schema-aware query generation.
 
Turns a natural-language question into a structured intent + parameters
that safe_query.py can execute. This NEVER lets free text reach SQL —
it only ever selects a whitelisted intent and validated parameters.
 
Two modes:
  1. Rule-based (default, always available, zero cost/no internet needed).
  2. LLM-assisted (optional): if OPENAI_API_KEY is set, ask an LLM to
     classify the question into the same structured schema via LangChain.
     The LLM output is still validated before use — it can only choose
     from the fixed set of intents below, never write raw SQL.
"""
 
import os
import re
import json
from dataclasses import dataclass, field
from typing import Optional
 
SUBJECT_NAME_TO_COLUMN = {
    "circuit theory": "subject1_marks",
    "digital electronics": "subject2_marks",
    "signals and systems": "subject3_marks",
    "data structures": "subject4_marks",
    "engineering maths": "subject5_marks",
    "engineering mathematics": "subject5_marks",
}
 
VALID_INTENTS = {
    "get_result",
    "get_attendance",
    "get_class_average",
    "get_top_performers",
    "get_failed_students",
    "get_class_summary",
    "retrieve_context",
    "unknown",
}
 
REG_NO_PATTERN = re.compile(r"\b(\d{9,15})\b")
 
 
@dataclass
class ParsedQuery:
    intent: str
    reg_no: Optional[str] = None
    subject_col: Optional[str] = None
    top_n: int = 5
    raw_question: str = ""
    extra: dict = field(default_factory=dict)
 
 
def _rule_based_parse(question: str) -> ParsedQuery:
    q = question.lower().strip()
    reg_match = REG_NO_PATTERN.search(q)
    reg_no = reg_match.group(1) if reg_match else None
 
    # Order matters: check more specific intents first.
    if any(kw in q for kw in ["top", "best", "rank", "topper"]):
        n_match = re.search(r"top\s+(\d+)", q)
        n = int(n_match.group(1)) if n_match else 5
        return ParsedQuery(intent="get_top_performers", top_n=n, raw_question=question)
 
    if any(kw in q for kw in ["fail", "failed", "backlog", "not passed"]):
        return ParsedQuery(intent="get_failed_students", raw_question=question)
 
    if any(kw in q for kw in ["class average", "average marks", "average for", "class performance", "summary"]):
        for name, col in SUBJECT_NAME_TO_COLUMN.items():
            if name in q:
                return ParsedQuery(intent="get_class_average", subject_col=col, raw_question=question)
        return ParsedQuery(intent="get_class_summary", raw_question=question)
 
    if "attendance" in q:
        return ParsedQuery(intent="get_attendance", reg_no=reg_no, raw_question=question)
 
    if any(kw in q for kw in ["result", "marks", "mark", "grade", "cgpa", "percentage", "score"]):
        return ParsedQuery(intent="get_result", reg_no=reg_no, raw_question=question)
 
    if reg_no:
        # A bare reg number with no clear keyword -> assume they want the result.
        return ParsedQuery(intent="get_result", reg_no=reg_no, raw_question=question)
 
    return ParsedQuery(intent="unknown", raw_question=question)
 
 
def _llm_assisted_parse(question: str) -> Optional[ParsedQuery]:
    """
    Optional LLM path. Only used if OPENAI_API_KEY is set. The LLM is asked
    to output STRICT JSON limited to the same whitelisted intents; anything
    outside that schema is rejected and we fall back to rule-based parsing.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        return None
 
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
 
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You classify a student's question into ONE JSON object with keys: "
             "intent (one of: get_result, get_attendance, get_class_average, "
             "get_top_performers, get_failed_students, get_class_summary, unknown), "
             "reg_no (string or null), subject_col (one of "
             f"{list(SUBJECT_NAME_TO_COLUMN.values())} or null), top_n (int, default 5). "
             "Reply with ONLY the JSON object, no other text."),
            ("user", "{question}"),
        ])
        chain = prompt | llm
        response = chain.invoke({"question": question})
        data = json.loads(response.content)
 
        intent = data.get("intent")
        if intent not in VALID_INTENTS:
            return None
 
        return ParsedQuery(
            intent=intent,
            reg_no=data.get("reg_no"),
            subject_col=data.get("subject_col"),
            top_n=int(data.get("top_n") or 5),
            raw_question=question,
        )
    except Exception:
        # Any failure (no package, no network, bad JSON) -> safely fall back.
        return None
 
 
def parse_question(question: str) -> ParsedQuery:
    llm_result = _llm_assisted_parse(question)
    if llm_result is not None:
        return llm_result
    return _rule_based_parse(question)