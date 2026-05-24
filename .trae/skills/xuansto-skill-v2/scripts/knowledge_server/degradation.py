import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .config import make_response, make_error_response
from .embedding import EmbeddingManager

logger = logging.getLogger("knowledge-server")


class DegradationManager:
    LEVEL_NORMAL = 0
    LEVEL_LOCAL_SEMANTIC = 1
    LEVEL_BM25_ONLY = 2
    LEVEL_FILE_SEARCH = 3

    LEVEL_NAMES = {0: "normal", 1: "local_semantic", 2: "bm25_only", 3: "file_search"}

    def __init__(self, chroma_engine, config, embedding_manager=None, sqlite_engine=None):
        self.chroma = chroma_engine
        self.config = config
        self.embedding_manager = embedding_manager
        self.sqlite = sqlite_engine
        self._level = self.LEVEL_NORMAL
        self._lock = threading.Lock()
        self._check_interval = 30
        self._running = False
        self._determine_initial_level()

    def _determine_initial_level(self):
        if self.embedding_manager:
            em_level = self.embedding_manager.level
            if em_level == EmbeddingManager.LEVEL_BM25_ONLY:
                self._level = self.LEVEL_BM25_ONLY
                logger.info("operation=degradation_init, level=bm25_only, reason=embedding_unavailable")
                return
            elif em_level == EmbeddingManager.LEVEL_LOCAL:
                self._level = self.LEVEL_LOCAL_SEMANTIC
                logger.info("operation=degradation_init, level=local_semantic, reason=embedding_local_only")
                return
        if not self.chroma.available:
            self._level = self.LEVEL_BM25_ONLY
            logger.info("operation=degradation_init, level=bm25_only, reason=chroma_unavailable")

    @property
    def level(self) -> int:
        with self._lock:
            return self._level

    @property
    def level_name(self) -> str:
        return self.LEVEL_NAMES.get(self.level, "unknown")

    def get_search_strategy(self) -> str:
        current = self.level
        if current == self.LEVEL_NORMAL:
            return "hybrid"
        elif current == self.LEVEL_LOCAL_SEMANTIC:
            return "hybrid"
        elif current == self.LEVEL_BM25_ONLY:
            return "keyword_only"
        else:
            return "file_search"

    def check_and_degrade(self) -> int:
        with self._lock:
            if self.sqlite is not None:
                try:
                    self.sqlite.count_entries()
                except Exception as e:
                    if self._level < self.LEVEL_FILE_SEARCH:
                        self._level = self.LEVEL_FILE_SEARCH
                        logger.warning("operation=degrade, level=file_search, reason=sqlite_unavailable, error=%s", e)
                    return self._level

            if self.embedding_manager:
                em_level = self.embedding_manager.level
                if em_level == EmbeddingManager.LEVEL_BM25_ONLY:
                    if self._level < self.LEVEL_BM25_ONLY:
                        self._level = self.LEVEL_BM25_ONLY
                        logger.warning("operation=degrade, level=bm25_only, reason=embedding_bm25_only")
                elif em_level == EmbeddingManager.LEVEL_LOCAL:
                    if self._level < self.LEVEL_LOCAL_SEMANTIC:
                        self._level = self.LEVEL_LOCAL_SEMANTIC
                        logger.warning("operation=degrade, level=local_semantic, reason=embedding_local")

            if self._level == self.LEVEL_NORMAL:
                if not self.chroma.available:
                    self._level = self.LEVEL_BM25_ONLY
                    logger.warning("operation=degrade, level=bm25_only, reason=chroma_unavailable")
                else:
                    try:
                        self.chroma.search_semantic("test", top_k=1)
                    except Exception:
                        self._level = self.LEVEL_LOCAL_SEMANTIC
                        logger.warning("operation=degrade, level=local_semantic, reason=vector_search_failed")

            return self._level

    def try_recover(self) -> int:
        with self._lock:
            recovered = False
            if self._level == self.LEVEL_FILE_SEARCH and self.sqlite is not None:
                try:
                    self.sqlite.count_entries()
                    self._level = self.LEVEL_BM25_ONLY
                    recovered = True
                    logger.info("operation=recover, level=bm25_only, reason=sqlite_recovered")
                except Exception:
                    return self._level

            if self.embedding_manager:
                self.embedding_manager.check_api_availability()
                em_level = self.embedding_manager.level
                if em_level == EmbeddingManager.LEVEL_API and self._level > self.LEVEL_NORMAL:
                    if self.chroma.available:
                        try:
                            self.chroma.search_semantic("test", top_k=1)
                            self._level = self.LEVEL_NORMAL
                            recovered = True
                            logger.info("operation=recover, level=normal")
                        except Exception:
                            pass
                elif em_level == EmbeddingManager.LEVEL_LOCAL and self._level > self.LEVEL_LOCAL_SEMANTIC:
                    self._level = self.LEVEL_LOCAL_SEMANTIC
                    recovered = True
                    logger.info("operation=recover, level=local_semantic")
            else:
                if self._level >= self.LEVEL_LOCAL_SEMANTIC:
                    if self.chroma.available:
                        try:
                            self.chroma.search_semantic("test", top_k=1)
                            self._level = self.LEVEL_NORMAL
                            recovered = True
                            logger.info("operation=recover, level=normal")
                        except Exception:
                            pass
            return self._level

    def start_periodic_check(self):
        if self._running:
            return
        self._running = True
        t = threading.Thread(target=self._periodic_check_loop, daemon=True)
        t.start()

    def stop_periodic_check(self):
        self._running = False

    def _periodic_check_loop(self):
        while self._running:
            time.sleep(self._check_interval)
            if self._level > self.LEVEL_NORMAL:
                self.try_recover()
            else:
                self.check_and_degrade()


class MCPToolFallback:
    SKILL_ROOT = Path(__file__).resolve().parent.parent.parent

    TOOL_SCRIPT_MAP = {
        "skill_analyze": {
            "script": "scripts/skill-test.py",
            "args": ["--analyze", "--format", "json"],
        },
        "quality_gate_check": {
            "script": "scripts/skill-test.py",
            "args": ["--gate", "--format", "json"],
        },
        "knowledge_search": {
            "script": "scripts/knowledge-server.py",
            "args": ["--search", "--format", "json"],
        },
        "knowledge_inject": {
            "script": "scripts/knowledge_server/main.py",
            "args": ["--inject", "--format", "json"],
        },
        "spec_drift_detect": {
            "script": "scripts/spec-drift-detector.py",
            "args": ["--format", "json"],
            "inline": "_inline_spec_drift_detect",
        },
        "security_scan": {
            "script": "scripts/agentic-security-scanner.py",
            "args": ["--format", "json"],
            "inline": "_inline_security_scan",
        },
        "code_simplify": {
            "script": "scripts/code-simplifier.py",
            "args": ["--format", "json"],
            "inline": "_inline_code_simplify",
        },
        "session_manage": {
            "scripts": {
                "init": ("scripts/init-session.py", []),
                "catchup": ("scripts/session-catchup.py", ["--format", "json"]),
                "persist": ("scripts/session-persist.py", []),
            },
        },
        "workflow_dispatch": {
            "scripts": {
                "start": ("scripts/project-initializer.py", []),
            },
            "inline": "_inline_workflow_dispatch",
        },
        "agent_status": {
            "script": "scripts/skill-test.py",
            "args": ["--agents", "--format", "json"],
            "inline": "_inline_agent_status",
        },
        "hook_manage": {
            "scripts": {
                "check_encoding": ("scripts/check-encoding.py", []),
                "token_budget": ("scripts/token-budget-guard.py", ["--check"]),
                "session_persist": ("scripts/session-persist.py", []),
            },
            "inline": "_inline_hook_manage",
        },
        "resource_load_status": {
            "inline": "_inline_resource_load_status",
        },
        "context_compress": {
            "script": "scripts/context-compressor.py",
            "args": ["--format", "json"],
        },
        "server_health": {
            "script": "scripts/health-checker.py",
            "args": ["--format", "json"],
            "inline": "_inline_server_health",
        },
    }

    def __init__(self, timeout: int = 120, skill_root: Optional[Path] = None):
        self._timeout = timeout
        self._skill_root = Path(skill_root) if skill_root else self.SKILL_ROOT
        self._degraded = False
        self._degradation_log: list = []
        self._lock = threading.Lock()

    @property
    def is_degraded(self) -> bool:
        with self._lock:
            return self._degraded

    @property
    def degradation_log(self) -> list:
        with self._lock:
            return list(self._degradation_log)

    def activate_degradation(self, reason: str = "mcp_unavailable"):
        with self._lock:
            self._degraded = True
            entry = {
                "event": "degradation_activated",
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._degradation_log.append(entry)
        logger.warning("operation=mcp_degradation_activate, reason=%s", reason)

    def deactivate_degradation(self):
        with self._lock:
            self._degraded = False
            entry = {
                "event": "degradation_deactivated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._degradation_log.append(entry)
        logger.info("operation=mcp_degradation_deactivate")

    def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> dict:
        if tool_name not in self.TOOL_SCRIPT_MAP:
            return make_error_response(
                "UNKNOWN_TOOL",
                f"Unknown tool: {tool_name}",
                {"tool_name": tool_name},
            )

        config = self.TOOL_SCRIPT_MAP[tool_name]
        arguments = arguments or {}

        if "script" in config:
            result = self._execute_script(
                config["script"],
                config.get("args", []),
                arguments,
            )
            if result.get("status") != "error":
                return result
            if "inline" in config:
                inline_method = getattr(self, config["inline"], None)
                if inline_method:
                    logger.info(
                        "operation=mcp_fallback_inline, tool=%s, reason=script_failed",
                        tool_name,
                    )
                    return inline_method(arguments)
            return result

        if "scripts" in config:
            sub_command = arguments.get("action", "init")
            script_entry = config["scripts"].get(sub_command)
            if script_entry:
                script_path, extra_args = script_entry
                result = self._execute_script(script_path, extra_args, arguments)
                if result.get("status") != "error":
                    return result
            if "inline" in config:
                inline_method = getattr(self, config["inline"], None)
                if inline_method:
                    logger.info(
                        "operation=mcp_fallback_inline, tool=%s, action=%s, reason=script_failed",
                        tool_name,
                        sub_command,
                    )
                    return inline_method(arguments)
            return make_error_response(
                "NO_FALLBACK",
                f"No fallback for tool={tool_name} action={sub_command}",
                {"tool_name": tool_name, "action": sub_command},
            )

        if "inline" in config:
            inline_method = getattr(self, config["inline"], None)
            if inline_method:
                return inline_method(arguments)

        return make_error_response(
            "NO_FALLBACK",
            f"No fallback available for tool: {tool_name}",
            {"tool_name": tool_name},
        )

    def _execute_script(
        self,
        script_rel_path: str,
        base_args: list,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> dict:
        script_path = self._skill_root / script_rel_path
        if not script_path.exists():
            logger.error(
                "operation=script_fallback, script=%s, status=not_found",
                script_rel_path,
            )
            return make_error_response(
                "SCRIPT_NOT_FOUND",
                f"Script not found: {script_rel_path}",
                {"script": script_rel_path},
            )

        cmd = [sys.executable, str(script_path)] + list(base_args)

        stdin_data = None
        if arguments:
            stdin_data = json.dumps(arguments)

        log_entry = {
            "event": "script_fallback_call",
            "script": script_rel_path,
            "args": base_args,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._degradation_log.append(log_entry)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=str(self._skill_root),
                input=stdin_data,
            )

            if result.returncode == 0:
                stdout = result.stdout.strip()
                if stdout:
                    try:
                        script_output = json.loads(stdout)
                        logger.info(
                            "operation=script_fallback, script=%s, status=success",
                            script_rel_path,
                        )
                        return make_response("ok", script_output)
                    except json.JSONDecodeError:
                        logger.warning(
                            "operation=script_fallback, script=%s, status=non_json_output",
                            script_rel_path,
                        )
                        return make_response("ok", {
                            "raw_output": stdout,
                            "format": "text",
                            "degraded": True,
                        })
                logger.info(
                    "operation=script_fallback, script=%s, status=success_empty",
                    script_rel_path,
                )
                return make_response("ok", {"degraded": True})
            else:
                stderr_preview = result.stderr[:1000] if result.stderr else ""
                logger.error(
                    "operation=script_fallback, script=%s, status=error, rc=%d, stderr=%s",
                    script_rel_path,
                    result.returncode,
                    stderr_preview,
                )
                return make_error_response(
                    "SCRIPT_ERROR",
                    f"Script exited with code {result.returncode}",
                    {
                        "script": script_rel_path,
                        "returncode": result.returncode,
                        "stderr": stderr_preview,
                    },
                )

        except subprocess.TimeoutExpired:
            logger.error(
                "operation=script_fallback, script=%s, status=timeout, timeout=%d",
                script_rel_path,
                self._timeout,
            )
            return make_error_response(
                "SCRIPT_TIMEOUT",
                f"Script timed out after {self._timeout}s",
                {"script": script_rel_path, "timeout": self._timeout},
            )
        except FileNotFoundError:
            logger.error(
                "operation=script_fallback, script=%s, status=not_executable",
                script_rel_path,
            )
            return make_error_response(
                "SCRIPT_NOT_EXECUTABLE",
                f"Python interpreter or script not found",
                {"script": script_rel_path, "python": sys.executable},
            )
        except Exception as e:
            logger.error(
                "operation=script_fallback, script=%s, status=exception, error=%s",
                script_rel_path,
                str(e),
            )
            return make_error_response(
                "SCRIPT_EXCEPTION",
                f"Script execution failed: {e}",
                {"script": script_rel_path, "error": str(e)},
            )

    def _inline_spec_drift_detect(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        spec_dir = self._skill_root / arguments.get("spec_dir", ".trae/specs")
        src_dir = self._skill_root / arguments.get("src_dir", ".")
        drift_items = []

        if spec_dir.exists():
            for spec_file in spec_dir.rglob("*.md"):
                spec_name = spec_file.stem
                found_impl = False
                for ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"):
                    candidates = list(src_dir.rglob(f"{spec_name}{ext}"))
                    if candidates:
                        found_impl = True
                        break
                if not found_impl:
                    drift_items.append({
                        "spec": str(spec_file.relative_to(self._skill_root)),
                        "status": "no_implementation_found",
                    })

        return make_response("ok", {
            "drift_detected": len(drift_items) > 0,
            "items": drift_items,
            "total": len(drift_items),
            "degraded": True,
        })

    def _inline_security_scan(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        target = self._skill_root / arguments.get("target", ".")
        findings = []
        sensitive_patterns = [
            (r'(?:api[_-]?key|secret|password|token)\s*[:=]\s*["\'][^"\']+["\']', "hardcoded_secret", "critical"),
            (r'eval\s*\(', "eval_usage", "high"),
            (r'subprocess\.call\s*\(\s*["\']', "shell_injection_risk", "high"),
            (r'os\.system\s*\(', "os_system_usage", "medium"),
        ]

        if target.exists():
            import re
            scan_exts = {".py", ".js", ".ts", ".yaml", ".yml", ".json", ".md"}
            for root, _dirs, files in os.walk(str(target)):
                if any(skip in root for skip in ("node_modules", ".git", "__pycache__", ".venv")):
                    continue
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in scan_exts:
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            for lineno, line in enumerate(fh, 1):
                                for pattern, rule_id, severity in sensitive_patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        findings.append({
                                            "file": os.path.relpath(fpath, str(self._skill_root)),
                                            "line": lineno,
                                            "rule_id": rule_id,
                                            "severity": severity,
                                        })
                    except OSError:
                        pass

        return make_response("ok", {
            "findings": findings[:50],
            "total": len(findings),
            "scanned_path": str(target),
            "degraded": True,
        })

    def _inline_code_simplify(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        target = self._skill_root / arguments.get("target", ".")
        opportunities = []

        if target.exists():
            try:
                import ast
            except ImportError:
                return make_response("ok", {
                    "opportunities": [],
                    "total": 0,
                    "degraded": True,
                    "error": "ast module unavailable",
                })

            for root, _dirs, files in os.walk(str(target)):
                if any(skip in root for skip in ("node_modules", ".git", "__pycache__", ".venv")):
                    continue
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                            source = fh.read()
                        tree = ast.parse(source)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                body_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                                if body_lines > 50:
                                    opportunities.append({
                                        "file": os.path.relpath(fpath, str(self._skill_root)),
                                        "function": node.name,
                                        "line": node.lineno,
                                        "type": "long_function",
                                        "lines": body_lines,
                                    })
                            elif isinstance(node, (ast.If, ast.For, ast.While)):
                                depth = 0
                                parent = node
                                while hasattr(parent, '_parent'):
                                    parent = parent._parent
                                    depth += 1
                                if depth >= 3:
                                    opportunities.append({
                                        "file": os.path.relpath(fpath, str(self._skill_root)),
                                        "line": node.lineno,
                                        "type": "deep_nesting",
                                        "depth": depth,
                                    })
                    except (OSError, SyntaxError):
                        pass

        return make_response("ok", {
            "opportunities": opportunities[:50],
            "total": len(opportunities),
            "degraded": True,
        })

    def _inline_workflow_dispatch(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        action = arguments.get("action", "status")
        phase = arguments.get("phase", 0)

        if action == "advance":
            next_phase = min(phase + 1, 8)
            return make_response("ok", {
                "action": "advance",
                "previous_phase": phase,
                "current_phase": next_phase,
                "degraded": True,
            })

        return make_response("ok", {
            "action": action,
            "current_phase": phase,
            "degraded": True,
        })

    def _inline_agent_status(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        agents_dir = self._skill_root / "agents"
        agent_list = []

        if agents_dir.exists():
            for layer_dir in sorted(agents_dir.iterdir()):
                if not layer_dir.is_dir():
                    continue
                for agent_file in sorted(layer_dir.glob("*.md")):
                    agent_list.append({
                        "name": agent_file.stem,
                        "layer": layer_dir.name,
                        "available": True,
                    })

        return make_response("ok", {
            "agents": agent_list,
            "total": len(agent_list),
            "degraded": True,
        })

    def _inline_hook_manage(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        action = arguments.get("action", "list")
        hooks_file = self._skill_root / "hooks" / "hooks.json"

        if action == "list":
            hooks = []
            if hooks_file.exists():
                try:
                    with open(str(hooks_file), "r", encoding="utf-8") as fh:
                        hooks_data = json.load(fh)
                    hooks = hooks_data if isinstance(hooks_data, list) else [hooks_data]
                except (json.JSONDecodeError, OSError):
                    pass
            return make_response("ok", {
                "hooks": hooks,
                "total": len(hooks),
                "degraded": True,
            })

        return make_response("ok", {
            "action": action,
            "status": "executed",
            "degraded": True,
        })

    def _inline_resource_load_status(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        arguments = arguments or {}
        state_file = self._skill_root / ".knowledge" / "resource_state.json"
        state = {}

        if state_file.exists():
            try:
                with open(str(state_file), "r", encoding="utf-8") as fh:
                    state = json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass

        state.setdefault("phase", 0)
        state.setdefault("degraded", True)
        return make_response("ok", state)

    def _inline_server_health(self, arguments: Optional[Dict[str, Any]] = None) -> dict:
        return make_response("ok", {
            "status": "degraded",
            "mcp_available": False,
            "fallback_active": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "degraded": True,
        })
