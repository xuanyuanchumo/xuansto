from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger("config")

_config_lock = threading.Lock()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _find_project_root() -> Path:
    current = Path.cwd()
    while True:
        if (current / ".trae").is_dir() or (current / ".git").is_dir():
            return current
        parent = current.parent
        if parent == current:
            return Path.cwd()
        current = parent

def _detect_skill_root() -> Path:
    _env = os.environ.get("SKILL_ROOT") or os.environ.get("XUANSTO_SKILL_ROOT")
    if _env:
        return Path(_env)
    project_root = _find_project_root()
    candidate = project_root / ".trae" / "skills" / "xuansto-skill-v2"
    if candidate.is_dir():
        return candidate
    return DATA_DIR

SKILL_ROOT = _detect_skill_root()

SCRIPTS_DIR = SKILL_ROOT / "scripts"
KNOWLEDGE_SERVER_DIR = SCRIPTS_DIR / "knowledge_server"
REFERENCES_DIR = SKILL_ROOT / "references"
AGENTS_DIR = SKILL_ROOT / "agents"
COMMANDS_DIR = SKILL_ROOT / "commands"

def _load_yaml_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except ImportError:
        return {}
    except Exception as exc:
        from .logging_config import get_logger
        get_logger("config").warning("Failed to load YAML config from %s: %s", config_path, exc)
        return {}

def _resolve_skill_file(filename: str) -> Path:
    primary = SKILL_ROOT / filename
    if primary.exists():
        return primary
    if SKILL_ROOT != DATA_DIR:
        fallback = DATA_DIR / filename
        if fallback.exists():
            return fallback
    return primary

DEFAULT_GATE_SCRIPTS_MAP = {
    "GATE-007": "check-encoding.py",
    "TEST-PASS": "coverage-check.py",
    "FILE-ENCODING": "check-encoding.py",
    "COMMENT-LANGUAGE": "check-comment-lang.py",
    "SCRIPT-SECURITY": "script-security-scanner.py",
}

DEFAULT_QUALITY_GATES_PHASE_MAP = {
    "0": ["DESIGN-SYSTEM-COMPLETE", "ANTI-PATTERN-CHECK", "DESIGN-REVIEW-PRODUCT", "DESIGN-REVIEW-TECH", "DESIGN-REVIEW-DESIGN"],
    "1": ["BRAINSTORM-COMPLETE", "GATE-001", "GATE-002"],
    "2": ["PLAN-ATOMIC", "GATE-003", "GATE-004"],
    "3": ["TEST-FIRST"],
    "4": ["SUBAGENT-REVIEW", "REVIEW-CONFIDENCE", "GATE-007", "TEST-PASS", "GATE-009", "FILE-ENCODING"],
    "5": ["PLAYWRIGHT-E2E-PASS", "GATE-011", "GATE-012", "AI-PENTEST", "SPEC-CONSISTENCY"],
    "6": ["GATE-013", "GATE-014", "INFRA-HEALTH", "UX-ACCEPTANCE"],
    "7": ["SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE", "GATE-015"],
    "8": ["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-UPDATE", "DESKTOP-CROSS", "IPC-CONTRACT"],
}

DEFAULT_HOOK_SCRIPTS_MAP = {
    "security-block": None,
    "token-budget-check": "token-budget-guard.py",
    "dangerous-cmd-confirm": None,
    "auto-format": None,
    "encoding-check": "check-encoding.py",
    "console-log-detect": None,
    "type-check": None,
    "load-context": "session-catchup.py",
    "kb-health-check": "health-checker.py",
    "platform-detect": "project-initializer.py",
    "session-save": "session-persist.py",
    "git-status-check": None,
    "experience-precipitate": "pattern-learner.py",
    "pattern-detect": "pattern-learner.py",
    "save-state": "session-persist.py",
    "decision-log-persist": None,
}

_CONFIG = _load_yaml_config(_resolve_skill_file(".xuansto-config.yaml"))

GATE_SCRIPTS_MAP = _CONFIG.get("gate_scripts", DEFAULT_GATE_SCRIPTS_MAP)
QUALITY_GATES_PHASE_MAP = _CONFIG.get("gates_by_phase", DEFAULT_QUALITY_GATES_PHASE_MAP)
HOOK_SCRIPTS_MAP = _CONFIG.get("hook_scripts", DEFAULT_HOOK_SCRIPTS_MAP)

def _validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    if "gate_scripts" in config and not isinstance(config["gate_scripts"], dict):
        errors.append("gate_scripts must be a dict")
    if "gates_by_phase" in config and not isinstance(config["gates_by_phase"], dict):
        errors.append("gates_by_phase must be a dict")
    if "hook_scripts" in config and not isinstance(config["hook_scripts"], dict):
        errors.append("hook_scripts must be a dict")
    return errors

def reload_config() -> dict[str, Any]:
    global GATE_SCRIPTS_MAP, QUALITY_GATES_PHASE_MAP, HOOK_SCRIPTS_MAP
    import yaml

    config_path = _resolve_skill_file(".xuansto-config.yaml")
    validation_warnings: list[str] = []

    if not config_path.exists():
        with _config_lock:
            GATE_SCRIPTS_MAP = DEFAULT_GATE_SCRIPTS_MAP
            QUALITY_GATES_PHASE_MAP = DEFAULT_QUALITY_GATES_PHASE_MAP
            HOOK_SCRIPTS_MAP = DEFAULT_HOOK_SCRIPTS_MAP
        return {
            "gate_scripts_count": len(GATE_SCRIPTS_MAP),
            "gates_by_phase_count": len(QUALITY_GATES_PHASE_MAP),
            "hook_scripts_count": len(HOOK_SCRIPTS_MAP),
            "validation_warnings": validation_warnings,
        }

    try:
        raw_text = config_path.read_text(encoding="utf-8")
        _new_config = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        logger.error("YAML parse error during config reload: %s", exc)
        return {
            "error": True,
            "code": "YAML_PARSE_ERROR",
            "message": str(exc),
            "validation_warnings": validation_warnings,
        }

    if not isinstance(_new_config, dict):
        _new_config = {}

    field_validators = {
        "gate_scripts": dict,
        "gates_by_phase": dict,
        "hook_scripts": dict,
    }
    for field, expected_type in field_validators.items():
        if field in _new_config and not isinstance(_new_config[field], expected_type):
            warning = f"{field} must be a {expected_type.__name__}, got {type(_new_config[field]).__name__}; using default"
            validation_warnings.append(warning)
            logger.warning("Config validation warning: %s", warning)
            del _new_config[field]

    with _config_lock:
        GATE_SCRIPTS_MAP = _new_config.get("gate_scripts", DEFAULT_GATE_SCRIPTS_MAP)
        QUALITY_GATES_PHASE_MAP = _new_config.get("gates_by_phase", DEFAULT_QUALITY_GATES_PHASE_MAP)
        HOOK_SCRIPTS_MAP = _new_config.get("hook_scripts", DEFAULT_HOOK_SCRIPTS_MAP)
    return {
        "gate_scripts_count": len(GATE_SCRIPTS_MAP),
        "gates_by_phase_count": len(QUALITY_GATES_PHASE_MAP),
        "hook_scripts_count": len(HOOK_SCRIPTS_MAP),
        "validation_warnings": validation_warnings,
    }

def _get_config_mtime() -> float:
    config_path = _resolve_skill_file(".xuansto-config.yaml")
    if config_path.exists():
        return config_path.stat().st_mtime
    return 0.0

_config_watcher_thread: threading.Thread | None = None
_config_watcher_stop = threading.Event()
_watchfiles_watcher: Any | None = None

_HAS_WATCHFILES = False
try:
    import watchfiles as _watchfiles_module
    _HAS_WATCHFILES = True
except ImportError:
    _HAS_WATCHFILES = False


def _config_watcher_poll() -> None:
    last_mtime = _get_config_mtime()
    while not _config_watcher_stop.is_set():
        _config_watcher_stop.wait(5.0)
        current_mtime = _get_config_mtime()
        if current_mtime != last_mtime and current_mtime > 0:
            last_mtime = current_mtime
            reload_config()


def _config_watcher_watchfiles() -> None:
    config_path = _resolve_skill_file(".xuansto-config.yaml")
    watch_dir = config_path.parent if config_path.exists() else SKILL_ROOT
    if not watch_dir.exists():
        _config_watcher_poll()
        return
    try:
        for _changes in _watchfiles_module.watch(watch_dir, stop_event=_config_watcher_stop):
            config_path_check = _resolve_skill_file(".xuansto-config.yaml")
            if config_path_check.exists():
                reload_config()
    except Exception as exc:
        logger.warning("watchfiles watcher failed, falling back to polling: %s", exc)
        _config_watcher_poll()


def _setup_signal_handler() -> None:
    if sys.platform == "win32":
        return
    import signal
    def _sighup_handler(signum: int, frame: Any) -> None:
        reload_config()
    signal.signal(signal.SIGHUP, _sighup_handler)

def start_config_watcher() -> None:
    global _config_watcher_thread
    _setup_signal_handler()
    target = _config_watcher_watchfiles if _HAS_WATCHFILES else _config_watcher_poll
    _config_watcher_thread = threading.Thread(target=target, daemon=True)
    _config_watcher_thread.start()
    if _HAS_WATCHFILES:
        logger.info("Config watcher started with watchfiles (event-driven)")
    else:
        logger.info("Config watcher started with thread polling (watchfiles not available)")

def stop_config_watcher() -> None:
    _config_watcher_stop.set()

WORK_DIR = Path(os.environ.get("XUANSTO_WORK_DIR", str(_find_project_root() / ".xuansto")))
SESSION_DIR = WORK_DIR / "sessions"
PATTERNS_DIR = WORK_DIR / "patterns"

WORKFLOWS_DIR = SKILL_ROOT / "workflows"
TEMPLATES_DIR = SKILL_ROOT / "templates"
HOOKS_PATH = SKILL_ROOT / "hooks" / "hooks.json"

KNOWLEDGE_DIR = DATA_DIR / "knowledge"
KNOWLEDGE_GENERAL_DIR = KNOWLEDGE_DIR / "general"
KNOWLEDGE_WORKSPACE_DIR = KNOWLEDGE_DIR / "workspace"
KNOWLEDGE_EXPERIENCE_DIR = KNOWLEDGE_DIR / "experience"
KNOWLEDGE_DB_PATH = KNOWLEDGE_DIR / "index" / "knowledge.db"
KNOWLEDGE_CHROMA_PATH = KNOWLEDGE_DIR / "index" / "chroma_db"

_CHROMA_LEGACY_PATH = KNOWLEDGE_DIR / "index" / "chroma"


def _migrate_chroma_path() -> None:
    legacy = _CHROMA_LEGACY_PATH
    current = KNOWLEDGE_CHROMA_PATH
    if not legacy.exists():
        return
    if not any(legacy.iterdir()):
        return
    if current.exists() and any(current.iterdir()):
        logger.warning(
            "Both legacy ChromaDB path (%s) and current path (%s) exist with data. "
            "Using current path. Please remove the legacy directory manually.",
            legacy, current,
        )
        return
    if current.exists():
        if not any(current.iterdir()):
            current.rmdir()
        else:
            logger.warning("Current ChromaDB path %s exists with data, skipping migration", current)
            return
    try:
        import shutil
        shutil.move(str(legacy), str(current))
        logger.info("Migrated ChromaDB data from %s to %s", legacy, current)
    except OSError as exc:
        logger.warning("Failed to migrate ChromaDB path from %s to %s: %s", legacy, current, exc)


_migrate_chroma_path()

MCP_API_VERSION = "3.0.0"
MCP_MIN_SUPPORTED_VERSION = "2.0.0"

API_CHANGELOG: dict[str, list[str]] = {
    "2.0.0": [
        "Pluggable search engine architecture (SearchEngine Protocol)",
        "HookEngine plugin system for dynamic hook registration",
        "YAML-based fallback/degradation configuration",
        "Event-driven config hot-reload via watchfiles",
        "Backward compatible with v1.0.0 clients",
    ],
    "3.0.0": [
        "Progressive loading with phase-based resource preloading",
        "Enhanced loading_progress action with feature availability and token budget tracking",
        "Cumulative phase preloading (loads all resources up to target phase)",
        "Phase history tracking with trigger information",
        "Backward compatible with v2.0.0 and v1.0.0 clients",
    ],
}
