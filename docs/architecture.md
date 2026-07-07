Architecture — Student Result Query Bot (PRJ-030)

Overview

A schema-aware bot that answers marks, attendance, and class-performance
queries from a student database. Built incrementally over 3 weeks:
Week 1 (knowledge base + basic chat), Week 2 (retrieval + citations),
Week 3 (access control + logging + UX polish).

Data Flow

User question (Streamlit chat, with role: student/admin)
        │
        ▼
FastAPI /query endpoint (main.py)
        │
        ▼
bot.py (orchestrator)
        │
        ├─► nlu.py            — schema-aware query generation:
        │                       question text -> (intent, reg_no, subject, ...)
        │                       Rule-based by default; optional LLM-assisted
        │                       parsing (LangChain) if OPENAI_API_KEY is set.
        │
        ├─► retrieval.py       — (Week 2) if no fixed intent matches, find the
        │                       most relevant student record via TF-IDF/FAISS
        │                       similarity search over the knowledge base.
        │
        ├─► access_control.py  — (Week 3) checks the caller's role before any
        │                       data is returned. Students can only see their
        │                       own result/attendance and class aggregates;
        │                       admins can see everything, including rankings.
        │
        ├─► safe_query.py      — whitelisted, parameterized SQL functions only.
        │                       Never executes raw SQL built from user input,
        │                       even for retrieval-matched records.
        │
        ├─► explain.py         — turns structured data into natural language.
        │                       Facts always come from safe_query.py; an
        │                       optional LLM pass only rephrases wording
        │                       (never alters numbers) and preserves citations.
        │
        └─► logging_store.py    — (Week 3) records every interaction
                                (question, intent, role, answer, timestamp)
                                to data/interaction_log.jsonl.
        │
        ▼
Response (answer + optional chart data) back to Streamlit UI

Why This Design Is "Safe"

The bot is schema-aware (it understands marks/attendance/performance
questions) but never lets free text become executable SQL. The only
things an LLM or NLU layer can choose are:


Which of a small, fixed set of Python functions to call (safe_query.py)
Which parameters to pass to it (always validated: e.g. top_n is
clamped to a safe range, subject columns are checked against a whitelist)


Even the Week 2 retrieval layer only ever identifies which student record
might be relevant — the actual marks/attendance numbers are always
re-fetched through the same safe, parameterized query functions, never
read directly out of the retrieved text.

Access Control Model (Week 3)

RoleOwn result/attendanceOther students' result/attendanceClass average / summaryTop performers / failed listStudent✅❌✅❌Admin✅✅✅✅

This is intentionally simple (no passwords/JWTs — out of scope for this
project) but demonstrates a real, testable access boundary.

Tech Stack


Backend: FastAPI
UI: Streamlit
Data store: SQLite (built from students.csv)
Retrieval: TF-IDF + cosine similarity (scikit-learn), with an
automatic upgrade path to FAISS + sentence-transformers if installed
Optional GenAI layer: LangChain + OpenAI, used only for flexible
question parsing and answer rephrasing — never for computing facts


Testing

26 automated tests across three suites (tests/test_bot.py,
tests/test_retrieval.py, tests/test_access_control.py), covering
data loading, intent parsing, retrieval relevance, citation correctness,
and access-control enforcement for both roles.