"""
test_retrieval.py
------------------
Week 2 testing plan: check answer relevance, citation correctness,
edge queries, and fallback handling.
 
Run with:
    python -m pytest tests/ -v
or, without pytest installed:
    python -m tests.test_retrieval
"""
 
import sys
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
from app import db_setup, retrieval
from app.bot import answer_question
 
 
def test_index_builds():
    db_setup.build_database()
    status = retrieval.rebuild_index()
    assert "rebuilt" in status.lower()
 
 
def test_retrieve_returns_ranked_results():
    results = retrieval.retrieve("student with low attendance struggling", k=3)
    assert isinstance(results, list)
    if len(results) > 1:
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
 
 
def test_retrieve_relevance_for_top_scorer_topic():
    # A question closely matching a specific known record should surface it
    # somewhere in the top results (not asserting rank #1 -- TF-IDF isn't
    # that precise on a tiny 20-row corpus, just that it's found at all).
    results = retrieval.retrieve("Charan Raj Circuit Theory Digital Electronics", k=5)
    reg_nos = [r["reg_no"] for r in results]
    assert "411723106003" in reg_nos
 
 
def test_fallback_produces_citation():
    response = answer_question("tell me about the student with excellent attendance and marks")
    assert response["intent"] in ("retrieve_context", "unknown")
    if response["intent"] == "retrieve_context":
        assert "[matched record:" in response["answer"]
 
 
def test_fallback_low_confidence_does_not_guess():
    response = answer_question("asdkjashd kjashdkjashd nonsense query xyz")
    # Should not confidently claim a match to gibberish.
    assert "[matched record:" not in response["answer"]
 
 
def test_exact_intents_still_bypass_retrieval():
    # Fixed intents should never go through the retrieval fallback path.
    response = answer_question("What is the result for 411723106003?")
    assert response["intent"] == "get_result"
    assert "[matched record:" not in response["answer"]
 
 
def test_admin_refresh_rebuilds_without_error():
    db_setup.build_database()
    status = retrieval.rebuild_index()
    assert status
 
 
if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__} -> {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
 