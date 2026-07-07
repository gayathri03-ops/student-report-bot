import sys
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
from app import db_setup, logging_store
from app.bot import answer_question
 
 
def setup_module(module=None):
    db_setup.build_database()
    logging_store.clear_log()
 
 
def test_admin_can_view_any_result():
    response = answer_question(
        "result for 411723106003", role="admin"
    )
    assert response["intent"] == "get_result"
    assert "Charan Raj" in response["answer"]
 
 
def test_student_can_view_own_result():
    response = answer_question(
        "result for 411723106003", role="student", own_reg_no="411723106003"
    )
    assert response["intent"] == "get_result"
    assert "Charan Raj" in response["answer"]
 
 
def test_student_cannot_view_others_result():
    response = answer_question(
        "result for 411723106003", role="student", own_reg_no="411723106099"
    )
    assert response["intent"] == "access_denied"
    assert "Access denied" in response["answer"]
 
 
def test_student_without_own_reg_no_is_denied():
    response = answer_question(
        "result for 411723106003", role="student", own_reg_no=None
    )
    assert response["intent"] == "access_denied"
 
 
def test_student_cannot_view_top_performers():
    response = answer_question(
        "top 5 performers", role="student", own_reg_no="411723106003"
    )
    assert response["intent"] == "access_denied"
 
 
def test_student_cannot_view_failed_students():
    response = answer_question(
        "list failed students", role="student", own_reg_no="411723106003"
    )
    assert response["intent"] == "access_denied"
 
 
def test_student_can_view_class_summary():
    # Aggregate-only data (no individual names) -- should be open to students.
    response = answer_question(
        "class performance summary", role="student", own_reg_no="411723106003"
    )
    assert response["intent"] == "get_class_summary"
    assert "Access denied" not in response["answer"]
 
 
def test_admin_can_view_top_performers():
    response = answer_question("top 5 performers", role="admin")
    assert response["intent"] == "get_top_performers"
    assert "Access denied" not in response["answer"]
 
 
def test_interactions_are_logged():
    logging_store.clear_log()
    answer_question("class performance summary", role="admin")
    answer_question("result for 411723106003", role="admin")
    recent = logging_store.read_recent_interactions(limit=10)
    assert len(recent) == 2
    assert recent[0]["question"] == "class performance summary"
    assert recent[1]["question"] == "result for 411723106003"
    assert "timestamp" in recent[0]
 
 
if __name__ == "__main__":
    setup_module()
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