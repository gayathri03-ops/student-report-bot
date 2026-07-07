# Student Result Query Bot (PRJ-030)

A schema-aware bot that answers marks, attendance, and class-performance queries from a student database — built with FastAPI, Streamlit, and an optional LangChain-powered NLU layer.

## Architecture

User question
-> Streamlit chat UI
-> FastAPI backend (/query)
-> nlu.py(schema-aware query generation: text -> intent + params)
-> safe_query.py (safe, whitelisted, parameterized SQL — no raw SQL from users)
-> explain.py(result explanation: structured data -> natural language)
-> back to the UI (with chart output for numeric results)
**Why this is "safe query execution":** the NLU layer can only ever pick
from a fixed set of whitelisted Python functions in `safe_query.py`. It
never builds or executes a raw SQL string from user input, so there's no
SQL-injection surface even though the bot is "schema-aware."

## Setup Instructions

1. **Clone the repo and create a virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
   pip install -r requirements.txt
```

3. **Build the database** (from `data/students.csv`)
```bash
   python -m app.db_setup
```

4. **Run the backend**
```bash
   uvicorn app.main:app --reload
```
   Visit `http://127.0.0.1:8000/docs` to try the API directly.

5. **Run the chat UI** (in a second terminal)
```bash
   streamlit run streamlit_app.py
```

## Sample Questions to Try

- "What is the result for 411723106003?"
- "What is the attendance for 411723106004?"
- "Who are the top 5 performers?"
- "List all failed students"
- "What is the class average in Circuit Theory?"
- "Give me the class performance summary"

## Running Tests

```bash
python -m pytest tests/ -v
# or, without pytest:
python -m tests.test_bot
```

## Project Structure
student-result-bot/
├── app/
│   ├── db_setup.py      # builds SQLite DB from CSV (the "knowledge base")
│   ├── safe_query.py    # whitelisted, parameterized query layer
│   ├── nlu.py            # schema-aware query generation (intent parsing)
│   ├── explain.py        # result explanation (structured data -> text)
│   ├── bot.py            # orchestrator: question -> answer
│   └── main.py            # FastAPI app
├── data/
│   └── students.csv      # sample/dummy student dataset
├── tests/
│   └── test_bot.py        # test cases
├── streamlit_app.py       # chat UI with chart output + saved prompts
├── requirements.txt
└── README.md

## Notes for Submission

- All data in `students.csv` is dummy/sample data — no real student
  records are used, per the assignment's data-privacy requirement.
- No API keys or credentials are hardcoded; `OPENAI_API_KEY` (if used)
  is read from an environment variable only.
- Regular, incremental GitHub commits are expected — commit after each
  file/feature above rather than in one final dump.
