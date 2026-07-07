import json
from datetime import datetime, timezone
from pathlib import Path
 
LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "interaction_log.jsonl"
 
 
def log_interaction(question: str, intent: str, role: str,
                     own_reg_no: str | None, answer: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "intent": intent,
        "role": role,
        "own_reg_no": own_reg_no,
        "answer": answer,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
 
 
def read_recent_interactions(limit: int = 20) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    recent = lines[-limit:]
    return [json.loads(line) for line in recent]
 
 
def clear_log() -> None:
    """Used mainly in tests, to keep the log file from growing unbounded."""
    if LOG_PATH.exists():
        LOG_PATH.unlink()
 