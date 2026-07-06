"""
retrieval.py
------------
Week 2: Retrieval layer over the knowledge base.
 
Turns each student's record into a text "document," embeds all documents,
and lets the bot find the most relevant record(s) for a freeform question
that doesn't match one of the fixed intents in nlu.py.
 
Two backends, same interface (`retrieve(query, k)`):
 
  1. TF-IDF + cosine similarity (default). Uses scikit-learn only —
     no internet connection, no model download, no API key required.
     This is what "FAISS/Chroma" is standing in for if those heavier
     dependencies aren't installed; it's the same retrieval *pattern*
     (embed documents, embed query, rank by similarity) with a lighter
     embedding method.
 
  2. FAISS + sentence-transformers (upgrade path). If both packages are
     installed, this is used instead automatically — same function
     signatures, so nothing else in the app needs to change.
 
IMPORTANT (safe query execution): retrieval only ever tells us WHICH
student record is relevant. It never returns marks/attendance numbers
directly to the user — those always come from safe_query.py. This keeps
the "no raw data straight from an unvetted source" guarantee even though
we've added a GenAI-style retrieval step on top.
"""
 
import pickle
import sqlite3
from pathlib import Path
from typing import Optional
 
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "students.db"
INDEX_PATH = BASE_DIR / "data" / "vector_store" / "tfidf_index.pkl"
 
_USE_FAISS = False
try:
    import faiss  # noqa: F401
    from sentence_transformers import SentenceTransformer  # noqa: F401
    _USE_FAISS = True
except ImportError:
    _USE_FAISS = False
 
 
def _load_student_documents() -> list[dict]:
    """Build one text 'document' per student record — the corpus to index."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
 
    docs = []
    for r in rows:
        subjects_text = "; ".join(
            f"{r[f'subject{i}_name']} {r[f'subject{i}_marks']} marks"
            for i in range(1, 6)
        )
        text = (
            f"Student {r['name']}, register number {r['reg_no']}, "
            f"department {r['department']}, semester {r['semester']}. "
            f"Subjects: {subjects_text}. "
            f"Total {r['total_marks']}/{r['max_marks']} ({r['percentage']}%). "
            f"Attendance {r['attendance_percent']}%. "
            f"Result: {r['result_status']}."
        )
        docs.append({"reg_no": str(r["reg_no"]), "text": text})
    return docs
 
 
# ---------------------------------------------------------------------
# Backend 1: TF-IDF (default, no internet required)
# ---------------------------------------------------------------------
 
def _build_tfidf_index() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
 
    docs = _load_student_documents()
    corpus = [d["text"] for d in docs]
 
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
 
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump({"vectorizer": vectorizer, "matrix": matrix, "docs": docs}, f)
 
 
def _retrieve_tfidf(query: str, k: int) -> list[dict]:
    from sklearn.metrics.pairwise import cosine_similarity
 
    if not INDEX_PATH.exists():
        _build_tfidf_index()
 
    with open(INDEX_PATH, "rb") as f:
        state = pickle.load(f)
 
    query_vec = state["vectorizer"].transform([query])
    scores = cosine_similarity(query_vec, state["matrix"])[0]
    ranked = sorted(
        zip(state["docs"], scores), key=lambda x: x[1], reverse=True
    )[:k]
    return [
        {"reg_no": doc["reg_no"], "text": doc["text"], "score": round(float(score), 3)}
        for doc, score in ranked
        if score > 0
    ]
 
 
# ---------------------------------------------------------------------
# Backend 2: FAISS + sentence-transformers (auto-used if installed)
# ---------------------------------------------------------------------
 
_faiss_index = None
_faiss_docs = None
_embedder = None
 
 
def _build_faiss_index() -> None:
    global _faiss_index, _faiss_docs, _embedder
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
 
    docs = _load_student_documents()
    _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = _embedder.encode([d["text"] for d in docs])
    embeddings = np.array(embeddings).astype("float32")
 
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
 
    _faiss_index = index
    _faiss_docs = docs
 
 
def _retrieve_faiss(query: str, k: int) -> list[dict]:
    import numpy as np
 
    if _faiss_index is None:
        _build_faiss_index()
 
    query_vec = _embedder.encode([query]).astype("float32")
    distances, indices = _faiss_index.search(np.array(query_vec), k)
 
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        doc = _faiss_docs[idx]
        # Convert L2 distance to a rough similarity-style score for consistency.
        score = round(float(1 / (1 + dist)), 3)
        results.append({"reg_no": doc["reg_no"], "text": doc["text"], "score": score})
    return results
 
 
# ---------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------
 
def rebuild_index() -> str:
    """Rebuild the retrieval index from the current database contents.
    Used by the admin refresh workflow."""
    if _USE_FAISS:
        _build_faiss_index()
        return "FAISS index rebuilt."
    else:
        _build_tfidf_index()
        return "TF-IDF index rebuilt."
 
 
def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return up to k most relevant student documents for a freeform query.
    Each result includes a 'score' used as the citation/confidence shown to the user."""
    if _USE_FAISS:
        return _retrieve_faiss(query, k)
    return _retrieve_tfidf(query, k)