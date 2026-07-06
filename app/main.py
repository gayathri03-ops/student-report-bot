"""
main.py
-------
FastAPI backend exposing the Student Result Query Bot as an API.
 
Run with:
    uvicorn app.main:app --reload
Then visit http://127.0.0.1:8000/docs for the interactive API docs.
"""
 
from fastapi import FastAPI
from pydantic import BaseModel
 
from app.bot import answer_question
from app import safe_query, db_setup, retrieval
 
app = FastAPI(
    title="Student Result Query Bot",
    description="Schema-aware bot that answers marks, attendance, and "
                 "class-performance queries from a student database.",
    version="1.0.0",
)
 
 
class QueryRequest(BaseModel):
    question: str
 
 
class QueryResponse(BaseModel):
    intent: str
    answer: str
    data: dict | list | None = None
 
 
@app.get("/")
def health_check():
    return {"status": "ok", "service": "student-result-query-bot"}
 
 
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = answer_question(request.question)
    return result
 
 
@app.get("/summary")
def summary():
    return safe_query.get_class_performance_summary()
 
 
@app.post("/admin/refresh")
def admin_refresh():
    """Admin refresh workflow (Week 2): rebuild the SQLite DB from the CSV
    and rebuild the retrieval index, without restarting the server. Use this
    after updating data/students.csv with new/changed records."""
    db_setup.build_database()
    index_status = retrieval.rebuild_index()
    return {
        "status": "refreshed",
        "database": "rebuilt from data/students.csv",
        "retrieval_index": index_status,
    }
 