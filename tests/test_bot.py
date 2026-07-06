"""
test_bot.py
-----------
Week 1 testing plan: test data loading, chunking/parsing, and baseline
Q&A flow on sample queries.

Run with:
    python -m pytest tests/ -v
or, without pytest installed:
    python -m tests.test_bot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db_setup, safe_query, nlu
from app.bot import answer_question


def test_database_builds_and_loads():
    db_setup.build_database()
    assert safe_query.DB_PATH.exists()


def test_valid_reg_no_returns_result():
    result = safe_query.get_student_result("411723106003")
    assert result is not None
    assert result["name"] == "Charan Raj"
    assert result["result_status"] == "PASS"


def test_invalid_reg_no_returns_none():
    result = safe_query.get_student_result("000000000000")
    assert result is None


def test_failing_student_detected_correctly():
    result = safe_query.get_student_result("411723106008")
    assert result["result_status"] == "FAIL"
    assert result["subjects_failed"] > 0


def test_nlu_extracts_reg_no():
    parsed = nlu.parse_question("What is the result for 411723106003?")
    assert parsed.intent == "get_result"
    assert parsed.reg_no == "411723106003"


def test_nlu_handles_unknown_input():
    parsed = nlu.parse_question("blah blah nonsense")
    assert parsed.intent == "unknown"


def test_end_to_end_result_query():
    response = answer_question("result for 411723106012")
    assert response["intent"] == "get_result"
    assert "Lavanya Shree" in response["answer"]
    assert "PASS" in response["answer"]


def test_end_to_end_unknown_reg_no():
    response = answer_question("result for 999999999999")
    assert "No student found" in response["answer"]


def test_end_to_end_class_summary():
    response = answer_question("give me the class summary")
    assert response["intent"] == "get_class_summary"
    assert "Pass rate" in response["answer"]


def test_top_performers_ordering():
    response = answer_question("top 3 performers")
    data = response["data"]
    percentages = [row["percentage"] for row in data]
    assert percentages == sorted(percentages, reverse=True)


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