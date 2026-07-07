from fastapi import FastAPI
from pydantic import BaseModel
 
from app.bot import answer_question
from app import safe_query, db_setup, retrieval, logging_store
 
app = FastAPI(
    title="Student Result Query Bot",
    description="Schema-aware bot that answers marks, attendance, and "
                 "class-performance queries from a student database.",
    version="1.0.0",
)
 
 
class QueryRequest(BaseModel):
    question: str
    role: str = "admin"          # "student" or "admin" (Week 3 access control)
    own_reg_no: str | None = None  # required if role == "student"
 
 
class QueryResponse(BaseModel):
    intent: str
    answer: str
    data: dict | list | None = None
 
 
@app.get("/")
def health_check():
    return {"status": "ok", "service": "student-result-query-bot"}
 
 
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    result = answer_question(request.question, role=request.role, own_reg_no=request.own_reg_no)
    return result
 
 
@app.get("/summary")
def summary():
    return safe_query.get_class_performance_summary()
 
 
@app.get("/history")
def history(limit: int = 20):
    """Week 3: view recent question/answer interaction history."""
    return logging_store.read_recent_interactions(limit=limit)
 
 
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
