#!/usr/bin/env python3
"""Session persistence helper for xuansto-skill v5.0.0"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
SESSION_DIR = SKILL_ROOT / ".skill-logs"
PATTERNS_DIR = SKILL_ROOT / ".knowledge" / "experience" / "patterns"

SESSION_TEMPLATE = """# Session {timestamp}

## 已完成任务
{completed}

## 未完成任务
{pending}

## 关键决策
{decisions}

## 经验沉淀
{experience}
"""

def save_session(completed_tasks=None, pending_tasks=None, decisions=None, experience=None):
    """Generate and save a session summary file."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"session-{timestamp}.md"
    filepath = SESSION_DIR / filename

    completed = "\n".join(f"- {t}" for t in (completed_tasks or [])) or "- (无)"
    pending = "\n".join(f"- {t}" for t in (pending_tasks or [])) or "- (无)"
    dec = "\n".join(f"- {d}" for d in (decisions or [])) or "- (无)"
    exp = "\n".join(f"- {e}" for e in (experience or [])) or "- (无)"

    content = SESSION_TEMPLATE.format(
        timestamp=timestamp,
        completed=completed,
        pending=pending,
        decisions=dec,
        experience=exp
    )

    filepath.write_text(content, encoding="utf-8")

    _cleanup_old_sessions()
    return str(filepath)

def load_last_session():
    """Load the most recent session summary."""
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    if not sessions:
        return None
    return sessions[0].read_text(encoding="utf-8")

def list_sessions():
    """List all session summary files."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    return [s.name for s in sessions]

def _cleanup_old_sessions(max_sessions=10):
    """Remove old session files beyond the limit."""
    sessions = sorted(SESSION_DIR.glob("session-*.md"), reverse=True)
    for old in sessions[max_sessions:]:
        old.unlink(missing_ok=True)

def detect_patterns(error_log=None):
    """Detect repeated error patterns from session data."""
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    if not error_log:
        return []

    error_counts = {}
    for error in error_log:
        key = error.strip()
        error_counts[key] = error_counts.get(key, 0) + 1

    patterns = []
    for error, count in error_counts.items():
        if count >= 2:
            pattern_file = PATTERNS_DIR / f"pattern-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            pattern_data = {
                "error": error,
                "count": count,
                "confidence": 0.40,
                "status": "draft",
                "created_at": datetime.now().isoformat(),
                "verified": False
            }
            pattern_file.write_text(json.dumps(pattern_data, ensure_ascii=False, indent=2), encoding="utf-8")
            patterns.append(pattern_data)

    return patterns

def verify_pattern(pattern_path, success=True):
    """Upgrade pattern confidence after successful application."""
    path = Path(pattern_path)
    if not path.exists():
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    if success:
        data["confidence"] = min(data.get("confidence", 0.40) + 0.05, 1.0)
        if data["confidence"] >= 0.80:
            data["status"] = "verified"
            data["verified"] = True

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: session-persist.py <save|load|list|detect|verify> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "save":
        path = save_session()
        print(f"Session saved: {path}")
    elif cmd == "load":
        content = load_last_session()
        if content:
            print(content)
        else:
            print("No sessions found")
    elif cmd == "list":
        for s in list_sessions():
            print(s)
    elif cmd == "detect":
        errors = sys.argv[2:] if len(sys.argv) > 2 else []
        patterns = detect_patterns(errors)
        print(f"Detected {len(patterns)} patterns")
    elif cmd == "verify":
        if len(sys.argv) < 3:
            print("Usage: session-persist.py verify <pattern_path> [success|failure]")
            sys.exit(1)
        result = verify_pattern(sys.argv[2], sys.argv[3] != "failure" if len(sys.argv) > 3 else True)
        print(f"Pattern updated: {result}")
    else:
        print(f"Unknown command: {cmd}")
