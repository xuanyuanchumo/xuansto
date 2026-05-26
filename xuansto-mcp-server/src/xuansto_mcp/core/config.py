from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any

from .logging_config import get_logger

logger = get_logger("config")

_config_lock = threading.Lock()

_CONFIG_VALIDATION_RESULTS: dict[str, dict[str, Any]] = {}

def _validate_config(data: dict, model_class: type, config_name: str) -> list[str]:
    errors: list[str] = []
    try:
        model_class(**data)
        _CONFIG_VALIDATION_RESULTS[config_name] = {"valid": True, "errors": []}
    except Exception as e:
        errors.append(str(e))
        logger.warning("Config validation failed for %s: %s. Using defaults where possible.", config_name, e)
        _CONFIG_VALIDATION_RESULTS[config_name] = {"valid": False, "errors": errors}
    return errors

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
    "SCRIPT-CLEANUP": "script-cleanup-checker.py",
    "DESIGN-TOKENS": "design-tokens-sync.js",
    "GATE-004": "api-contract-validator.py",
    "SPEC-CONSISTENCY": "spec-drift-detector.py",
    "AGENTIC-SECURITY": "agentic-security-scanner.py",
    "AI-PENTEST": "ai-pentest-runner.py",
    "VISUAL-REGRESSION": "visual-regression.js",
    "ACCESSIBILITY": "accessibility-test.js",
    "PERFORMANCE": "performance-benchmark.js",
    "DOC-COMPLETENESS": "documentation-coverage.py",
    "IPC-CONTRACT": "ipc-contract-validator.js",
    "ITERATION-BUDGET": "loop-guard.py",
    "SESSION-RECOVERY": "session-catchup.py",
    "DESKTOP-BUILD": "build-desktop.ps1",
    "DESKTOP-SIGN": "sign-desktop.ps1",
    "DESKTOP-UPDATE": "verify-auto-update.ps1",
    "TOKEN-BUDGET": "token-budget-guard.py",
    "SECURITY-FIX-CLOSED": "security-fix-closure.py",
}

DEFAULT_QUALITY_GATES_PHASE_MAP = {
    "0": ["DESIGN-REVIEW-PRODUCT", "DESIGN-REVIEW-TECH", "DESIGN-REVIEW-DESIGN", "DESIGN-TOKENS", "DESIGN-SYSTEM-COMPLETE", "ANTI-PATTERN-CHECK"],
    "1": ["GATE-001", "GATE-002", "BRAINSTORM-COMPLETE"],
    "2": ["GATE-003", "GATE-004", "PLAN-ATOMIC", "SPEC-ATOMIC"],
    "3": ["TEST-FIRST"],
    "4": ["GATE-007", "TEST-PASS", "GATE-009", "MULTI-PERSPECTIVE-COVERAGE", "TDD-RED", "TDD-GREEN", "TDD-REFACTOR", "EXECUTION-VERIFY", "SCRIPT-SECURITY", "SCRIPT-CLEANUP", "FILE-ENCODING", "COMMENT-LANGUAGE"],
    "5": ["GATE-011", "GATE-012", "SPEC-CONSISTENCY", "AGENTIC-SECURITY", "AI-PENTEST", "VISUAL-REGRESSION", "RENDER-CHECK", "ACCESSIBILITY", "PERFORMANCE", "SECURITY-FIX-CLOSED", "PLAYWRIGHT-E2E-PASS"],
    "6": ["GATE-013", "GATE-014", "UX-ACCEPTANCE", "DOD-CHECK", "INFRA-HEALTH"],
    "7": ["GATE-015", "DOC-COMPLETENESS", "SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE", "SCRIPT-CLEANUP"],
    "8": ["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-UPDATE", "DESKTOP-CROSS", "IPC-CONTRACT"],
    "cross": ["TOKEN-BUDGET", "ITERATION-BUDGET", "SESSION-RECOVERY", "BUILD-SUCCESS", "ROLLBACK-SAFETY", "INIT-COMPLETE", "STATUS-HEALTHY"],
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

_CONSTRAINTS_CONFIG = _load_yaml_config(_resolve_skill_file("constraints.yaml"))
_SKILL_CONFIG = _load_yaml_config(_resolve_skill_file(".skill-config.yaml"))

GATE_SCRIPTS_MAP = _CONFIG.get("gate_scripts", DEFAULT_GATE_SCRIPTS_MAP)
QUALITY_GATES_PHASE_MAP = _CONFIG.get("gates_by_phase", DEFAULT_QUALITY_GATES_PHASE_MAP)
HOOK_SCRIPTS_MAP = _CONFIG.get("hook_scripts", DEFAULT_HOOK_SCRIPTS_MAP)

_DEGRADATION_CONFIG = _CONFIG.get("degradation", {})
if not isinstance(_DEGRADATION_CONFIG, dict):
    _DEGRADATION_CONFIG = {}
DEGRADATION_HEALTH_CHECK_INTERVAL: float = _DEGRADATION_CONFIG.get("health_check_interval", 30.0)

def _validate_config_legacy(config: dict) -> list[str]:
    errors: list[str] = []
    if "gate_scripts" in config and not isinstance(config["gate_scripts"], dict):
        errors.append("gate_scripts must be a dict")
    if "gates_by_phase" in config and not isinstance(config["gates_by_phase"], dict):
        errors.append("gates_by_phase must be a dict")
    if "hook_scripts" in config and not isinstance(config["hook_scripts"], dict):
        errors.append("hook_scripts must be a dict")
    return errors

def _load_constraints() -> dict[str, Any]:
    global _CONSTRAINTS_CONFIG
    path = _resolve_skill_file("constraints.yaml")
    if not path.exists():
        logger.debug("constraints.yaml not found at %s, keeping current config", path)
        return {"loaded": False, "reason": "file_not_found", "path": str(path)}
    try:
        import yaml
        new_config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(new_config, dict):
            new_config = {}
        old_keys = set(_CONSTRAINTS_CONFIG.keys())
        new_keys = set(new_config.keys())
        changed_fields = sorted((old_keys ^ new_keys) | {k for k in old_keys & new_keys if _CONSTRAINTS_CONFIG.get(k) != new_config.get(k)})
        _CONSTRAINTS_CONFIG = new_config
        logger.info("Reloaded constraints.yaml from %s", path)
        return {"loaded": True, "path": str(path), "changed_fields": changed_fields}
    except Exception as exc:
        logger.warning("Failed to load constraints.yaml: %s", exc)
        return {"loaded": False, "reason": str(exc), "path": str(path)}


def _load_skill_config() -> dict[str, Any]:
    global _SKILL_CONFIG
    path = _resolve_skill_file(".skill-config.yaml")
    if not path.exists():
        logger.debug(".skill-config.yaml not found at %s, keeping current config", path)
        return {"loaded": False, "reason": "file_not_found", "path": str(path)}
    try:
        import yaml
        new_config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(new_config, dict):
            new_config = {}
        old_keys = set(_SKILL_CONFIG.keys())
        new_keys = set(new_config.keys())
        changed_fields = sorted((old_keys ^ new_keys) | {k for k in old_keys & new_keys if _SKILL_CONFIG.get(k) != new_config.get(k)})
        _SKILL_CONFIG = new_config
        logger.info("Reloaded .skill-config.yaml from %s", path)
        return {"loaded": True, "path": str(path), "changed_fields": changed_fields}
    except Exception as exc:
        logger.warning("Failed to load .skill-config.yaml: %s", exc)
        return {"loaded": False, "reason": str(exc), "path": str(path)}


def _notify_config_change(file_name: str, changed_fields: list[str]) -> None:
    from datetime import datetime, timezone

    from .notifications import notify
    timestamp = datetime.now(timezone.utc).isoformat()
    notify(
        f"Config file changed: {file_name} | fields: {', '.join(changed_fields) if changed_fields else 'none'} | at: {timestamp}",
        "info",
    )
    logger.info("Config change notification: file=%s, fields=%s, timestamp=%s", file_name, changed_fields, timestamp)


def reload_config() -> dict[str, Any]:
    global GATE_SCRIPTS_MAP, QUALITY_GATES_PHASE_MAP, HOOK_SCRIPTS_MAP, DEGRADATION_HEALTH_CHECK_INTERVAL
    import yaml

    config_path = _resolve_skill_file(".xuansto-config.yaml")
    validation_warnings: list[str] = []
    reload_details: dict[str, Any] = {}

    if not config_path.exists():
        with _config_lock:
            GATE_SCRIPTS_MAP = DEFAULT_GATE_SCRIPTS_MAP
            QUALITY_GATES_PHASE_MAP = DEFAULT_QUALITY_GATES_PHASE_MAP
            HOOK_SCRIPTS_MAP = DEFAULT_HOOK_SCRIPTS_MAP
            DEGRADATION_HEALTH_CHECK_INTERVAL = 30.0
        constraints_result = _load_constraints()
        skill_config_result = _load_skill_config()
        reload_details["constraints"] = constraints_result
        reload_details["skill_config"] = skill_config_result
        return {
            "gate_scripts_count": len(GATE_SCRIPTS_MAP),
            "gates_by_phase_count": len(QUALITY_GATES_PHASE_MAP),
            "hook_scripts_count": len(HOOK_SCRIPTS_MAP),
            "validation_warnings": validation_warnings,
            "reload_details": reload_details,
        }

    try:
        raw_text = config_path.read_text(encoding="utf-8")
        _new_config = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        logger.error("YAML parse error during config reload: %s", exc)
        return {
            "status": "error",
            "data": None,
            "error": {"code": "YAML_PARSE_ERROR", "message": str(exc), "validation_warnings": validation_warnings},
            "metadata": {},
        }

    if not isinstance(_new_config, dict):
        _new_config = {}

    field_validators = {
        "gate_scripts": dict,
        "gates_by_phase": dict,
        "hook_scripts": dict,
        "degradation": dict,
    }
    changed_fields: list[str] = []
    for field, expected_type in field_validators.items():
        if field in _new_config and not isinstance(_new_config[field], expected_type):
            warning = f"{field} must be a {expected_type.__name__}, got {type(_new_config[field]).__name__}; using default"
            validation_warnings.append(warning)
            logger.warning("Config validation warning: %s", warning)
            del _new_config[field]
        else:
            old_val = _CONFIG.get(field)
            new_val = _new_config.get(field)
            if old_val != new_val:
                changed_fields.append(field)

    try:
        from ..models.config_models import SkillConfigModel
        pydantic_errors = _validate_config(_new_config, SkillConfigModel, ".xuansto-config.yaml")
        validation_warnings.extend(pydantic_errors)
    except ImportError:
        pass

    with _config_lock:
        GATE_SCRIPTS_MAP = _new_config.get("gate_scripts", DEFAULT_GATE_SCRIPTS_MAP)
        QUALITY_GATES_PHASE_MAP = _new_config.get("gates_by_phase", DEFAULT_QUALITY_GATES_PHASE_MAP)
        HOOK_SCRIPTS_MAP = _new_config.get("hook_scripts", DEFAULT_HOOK_SCRIPTS_MAP)
        _new_degradation = _new_config.get("degradation", {})
        if not isinstance(_new_degradation, dict):
            _new_degradation = {}
        DEGRADATION_HEALTH_CHECK_INTERVAL = _new_degradation.get("health_check_interval", 30.0)

    if changed_fields:
        _notify_config_change(".xuansto-config.yaml", changed_fields)

    constraints_result = _load_constraints()
    skill_config_result = _load_skill_config()
    reload_details["constraints"] = constraints_result
    reload_details["skill_config"] = skill_config_result

    if constraints_result.get("loaded") and constraints_result.get("changed_fields"):
        _notify_config_change("constraints.yaml", constraints_result["changed_fields"])
    if skill_config_result.get("loaded") and skill_config_result.get("changed_fields"):
        _notify_config_change(".skill-config.yaml", skill_config_result["changed_fields"])

    return {
        "gate_scripts_count": len(GATE_SCRIPTS_MAP),
        "gates_by_phase_count": len(QUALITY_GATES_PHASE_MAP),
        "hook_scripts_count": len(HOOK_SCRIPTS_MAP),
        "validation_warnings": validation_warnings,
        "reload_details": reload_details,
    }

def _get_config_mtime() -> float:
    config_path = _resolve_skill_file(".xuansto-config.yaml")
    constraints_path = _resolve_skill_file("constraints.yaml")
    skill_config_path = _resolve_skill_file(".skill-config.yaml")
    mtimes = []
    if config_path.exists():
        mtimes.append(config_path.stat().st_mtime)
    if constraints_path.exists():
        mtimes.append(constraints_path.stat().st_mtime)
    if skill_config_path.exists():
        mtimes.append(skill_config_path.stat().st_mtime)
    return max(mtimes) if mtimes else 0.0

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
    watched_files = {".xuansto-config.yaml", "constraints.yaml", ".skill-config.yaml"}
    try:
        for changes in _watchfiles_module.watch(watch_dir, stop_event=_config_watcher_stop):
            changed_watched = {Path(c[1]).name for c in changes} & watched_files
            if changed_watched:
                logger.info("Config watcher detected changes in: %s", ", ".join(sorted(changed_watched)))
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
KNOWLEDGE_DB_PATH = WORK_DIR / "xuansto.db"
KNOWLEDGE_CHROMA_PATH = KNOWLEDGE_DIR / "index" / "chroma_db"

if not KNOWLEDGE_CHROMA_PATH.exists():
    logger.warning("KNOWLEDGE_CHROMA_PATH does not exist: %s", KNOWLEDGE_CHROMA_PATH)

if not AGENTS_DIR.exists():
    logger.warning("AGENTS_DIR does not exist: %s", AGENTS_DIR)

if not REFERENCES_DIR.exists():
    logger.warning("REFERENCES_DIR does not exist: %s", REFERENCES_DIR)

if not COMMANDS_DIR.exists():
    logger.warning("COMMANDS_DIR does not exist: %s", COMMANDS_DIR)

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
SKILL_MIN_VERSION = "8.0.0"

KNOWLEDGE_VERSION_CLEANUP_KEEP_LAST_N: int = int(os.environ.get("XUANSTO_KNOWLEDGE_CLEANUP_KEEP_LAST_N", "10"))

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


def parse_version(version_str: str) -> tuple[int, int, int]:
    parts = version_str.lstrip("v").split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def _merge_configs(user_config: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in user_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_configs(value, merged[key])
        else:
            merged[key] = value
    return merged
