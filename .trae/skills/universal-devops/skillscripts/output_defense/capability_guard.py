"""
原生能力约束层（第二维防线）- Capability Guard

提供工具调用权限白名单、API调用频率限制（令牌桶算法）、
文件操作沙箱、终端命令安全过滤等能力边界控制能力。
"""

from __future__ import annotations

import os
import re
import time
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class Action(Enum):
    """安全动作枚举"""

    ALLOW = auto()
    DENY = auto()
    AUDIT = auto()


PermissionPolicy = dict[str, Action]
RateLimitConfig = dict[str, int]
SandboxConfig = dict[str, Any]


@dataclass
class TokenBucket:
    """
    令牌桶算法实现

    用于API调用频率限制，支持可配置的填充速率和桶容量。
    """

    rate: float = 10.0
    capacity: int = 20
    _tokens: float = field(init=False, repr=False)
    _last_refill: float = field(init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        self._tokens = float(self.capacity)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def available_tokens(self) -> int:
        with self._lock:
            self._refill()
            return int(self._tokens)

    def reset(self) -> None:
        with self._lock:
            self._tokens = float(self.capacity)
            self._last_refill = time.monotonic()


@dataclass
class ToolPermissionManager:
    """
    工具调用权限白名单管理器

    维护允许/禁止的工具列表，支持按工具名称进行细粒度权限控制。
    """

    allowlist: set[str] = field(default_factory=set)
    denylist: set[str] = field(default_factory=set)
    default_action: Action = Action.DENY
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def allow_tool(self, tool_name: str) -> None:
        self.allowlist.add(tool_name)
        self.denylist.discard(tool_name)

    def deny_tool(self, tool_name: str) -> None:
        self.denylist.add(tool_name)
        self.allowlist.discard(tool_name)

    def check_permission(self, tool_name: str) -> tuple[Action, str]:
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        if tool_name in self.denylist:
            result = (Action.DENY, f"Tool '{tool_name}' is explicitly denied")
        elif tool_name in self.allowlist:
            result = (Action.ALLOW, f"Tool '{tool_name}' is allowed")
        else:
            result = (self.default_action, f"Tool '{tool_name}' uses default policy: {self.default_action.name}")
        self.audit_log.append({"timestamp": timestamp, "tool": tool_name, "action": result[0].name, "reason": result[1]})
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        return result

    def get_policy(self) -> PermissionPolicy:
        policy: PermissionPolicy = {}
        for t in self.allowlist:
            policy[t] = Action.ALLOW
        for t in self.denylist:
            policy[t] = Action.DENY
        return policy

    def clear_audit_log(self) -> None:
        self.audit_log.clear()


@dataclass
class RateLimiter:
    """
    API调用频率限制器（基于令牌桶）

    支持多维度限流：全局、按用户、按端点。
    """

    global_bucket: TokenBucket = field(default_factory=lambda: TokenBucket(rate=100.0, capacity=200))
    per_user_buckets: dict[str, TokenBucket] = field(default_factory=dict)
    per_endpoint_buckets: dict[str, TokenBucket] = field(default_factory=dict)
    default_user_rate: float = 30.0
    default_user_capacity: int = 60
    default_endpoint_rate: float = 50.0
    default_endpoint_capacity: int = 100

    def check_rate_limit(
        self,
        user_id: str = "",
        endpoint: str = "",
        tokens: int = 1,
    ) -> tuple[bool, str]:
        if not self.global_bucket.consume(tokens):
            return False, "Global rate limit exceeded"
        if user_id:
            bucket = self.per_user_buckets.get(user_id)
            if bucket is None:
                bucket = TokenBucket(rate=self.default_user_rate, capacity=self.default_user_capacity)
                self.per_user_buckets[user_id] = bucket
            if not bucket.consume(tokens):
                return False, f"Rate limit exceeded for user '{user_id}'"
        if endpoint:
            bucket = self.per_endpoint_buckets.get(endpoint)
            if bucket is None:
                bucket = TokenBucket(rate=self.default_endpoint_rate, capacity=self.default_endpoint_capacity)
                self.per_endpoint_buckets[endpoint] = bucket
            if not bucket.consume(tokens):
                return False, f"Rate limit exceeded for endpoint '{endpoint}'"
        return True, "OK"

    def get_stats(self) -> dict[str, Any]:
        return {
            "global_tokens": self.global_bucket.available_tokens,
            "global_capacity": self.global_bucket.capacity,
            "active_user_buckets": len(self.per_user_buckets),
            "active_endpoint_buckets": len(self.per_endpoint_buckets),
        }

    def reset_all(self) -> None:
        self.global_bucket.reset()
        for bucket in self.per_user_buckets.values():
            bucket.reset()
        for bucket in self.per_endpoint_buckets.values():
            bucket.reset()

    def remove_user(self, user_id: str) -> None:
        self.per_user_buckets.pop(user_id, None)

    def remove_endpoint(self, endpoint: str) -> None:
        self.per_endpoint_buckets.pop(endpoint, None)


@dataclass
class FileSandbox:
    """
    文件操作沙箱

    限制文件访问路径范围，防止路径穿越攻击。
    """

    allowed_roots: list[Path] = field(default_factory=list)
    deny_patterns: list[str] = field(
        default_factory=lambda: [
            r"\.\.",
            r"\0",
            r"\\",
            r"/etc/passwd",
            r"/etc/shadow",
            r"C:\\Windows\\System32\\config",
        ]
    )
    read_only_paths: set[Path] = field(default_factory=set)
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def add_allowed_root(self, root_path: Path | str) -> None:
        p = Path(root_path).resolve()
        if p not in self.allowed_roots:
            self.allowed_roots.append(p)

    def remove_allowed_root(self, root_path: Path | str) -> None:
        p = Path(root_path).resolve()
        self.allowed_roots = [r for r in self.allowed_roots if r != p]

    def add_read_only(self, path: Path | str) -> None:
        self.read_only_paths.add(Path(path).resolve())

    def is_path_allowed(self, target_path: Path | str, operation: str = "read") -> tuple[bool, str]:
        try:
            target = Path(target_path).resolve()
        except (OSError, ValueError):
            return False, f"Invalid path: {target_path}"
        target_str = str(target)
        for pattern in self.deny_patterns:
            if re.search(pattern, target_str, re.IGNORECASE):
                return False, f"Path matches deny pattern: {pattern}"
        if not self.allowed_roots:
            return True, "No restrictions configured"
        is_under_any_root = any(
            target == root or str(target).startswith(str(root) + os.sep)
            for root in self.allowed_roots
        )
        if not is_under_any_root:
            return False, f"Path outside allowed roots: {target}"
        if operation in ("write", "delete", "modify") and target in self.read_only_paths:
            return False, f"Path is read-only: {target}"
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        self.audit_log.append({
            "timestamp": timestamp,
            "path": target_str,
            "operation": operation,
            "allowed": True,
        })
        return True, "OK"

    def normalize_path(self, raw_path: str) -> Path:
        expanded = os.path.expandvars(os.path.expanduser(raw_path))
        return Path(expanded).resolve()


@dataclass
class CommandSecurityFilter:
    """
    终端命令安全过滤器

    使用黑名单机制过滤危险命令，防止恶意操作。
    """

    danger_patterns: list[tuple[str, str]] = field(default_factory=lambda: [
        (r"rm\s+-rf\s+/$|rm\s+-rf\s+/\s", "Destructive recursive delete on root"),
        (r"rm\s+-rf\s+[~]", "Destructive recursive delete on home directory"),
        (r"DROP\s+(TABLE|DATABASE)\s+", "SQL destructive operation"),
        (r"TRUNCATE\s+(TABLE|DATABASE)\s+", "SQL truncation operation"),
        (r"FORMAT\s+\w+:", "Disk format operation"),
        (r"mkfs\.", "Filesystem creation"),
        (r"dd\s+if=.+=/dev/", "Direct disk write"),
        (r">\s*/dev/sd[a-z]", "Overwrite disk device"),
        (r"chmod\s+-R\s+777", "Insecure permission change"),
        (r"chown\s+-R", "Recursive ownership change"),
        (r":(){.*};:", "Fork bomb pattern"),
        (r"curl.*\|\s*(bash|sh|python|perl)", "Remote code execution via pipe"),
        (r"wget.*\|\s*(bash|sh|python|perl)", "Remote code execution via pipe"),
        (r"eval\s*\(", "Dynamic code evaluation"),
        (r"__import__\s*\(", "Dynamic module import"),
        (r"exec\s*\(", "Code execution function"),
        (r"subprocess\.call\(.*shell=True", "Shell injection risk"),
        (r"os\.system\s*\(", "OS command execution"),
        (r"shutdown\b", "System shutdown command"),
        (r"reboot\b", "System reboot command"),
        (r"halt\b", "System halt command"),
        (r"init\s+0", "System runlevel change to halt"),
        (r"reg\s+delete\s+HKLM", "Windows registry deletion"),
        (r"bcdedit.*delete", "Boot configuration deletion"),
    ])
    allow_patterns: list[str] = field(default_factory=list)
    case_sensitive: bool = False
    audit_log: list[dict[str, Any]] = field(default_factory=list)

    def add_danger_pattern(self, pattern: str, description: str = "") -> None:
        self.danger_patterns.append((pattern, description or f"Custom: {pattern}"))

    def add_allow_pattern(self, pattern: str) -> None:
        self.allow_patterns.append(pattern)

    def is_command_safe(self, command: str) -> tuple[bool, list[str]]:
        issues: list[str] = []
        flags = re.IGNORECASE if not self.case_sensitive else 0
        for allow_pattern in self.allow_patterns:
            if re.search(allow_pattern, command, flags):
                return True, []
        for pattern, description in self.danger_patterns:
            if re.search(pattern, command, flags):
                issues.append(f"[BLOCKED] {description} (pattern: {pattern})")
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        self.audit_log.append({
            "timestamp": timestamp,
            "command": command[:200],
            "safe": len(issues) == 0,
            "issues": issues,
        })
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
        return len(issues) == 0, issues

    def sanitize_command(self, command: str) -> str:
        safe, issues = self.is_command_safe(command)
        if safe:
            return command
        sanitized = command
        flags = re.IGNORECASE if not self.case_sensitive else 0
        for pattern, _ in self.danger_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=flags)
        return sanitized


@dataclass
class CapabilityGuard:
    """
    原生能力约束层 - 第二维输出防线

    职责：
      - 工具调用权限白名单管理
      - API调用频率限制（令牌桶算法）
      - 文件操作沙箱（路径穿越防护）
      - 终端命令安全过滤（危险命令黑名单）
    """

    tool_permissions: ToolPermissionManager = field(default_factory=ToolPermissionManager)
    rate_limiter: RateLimiter = field(default_factory=RateLimiter)
    file_sandbox: FileSandbox = field(default_factory=FileSandbox)
    command_filter: CommandSecurityFilter = field(default_factory=CommandSecurityFilter)
    enabled: bool = True

    def is_command_safe(self, command: str) -> tuple[bool, list[str]]:
        if not self.enabled:
            return True, []
        return self.command_filter.is_command_safe(command)

    def is_path_allowed(self, target_path: Path | str, operation: str = "read") -> tuple[bool, str]:
        if not self.enabled:
            return True, "Guard disabled"
        return self.file_sandbox.is_path_allowed(target_path, operation)

    def check_rate_limit(
        self,
        user_id: str = "",
        endpoint: str = "",
        tokens: int = 1,
    ) -> tuple[bool, str]:
        if not self.enabled:
            return True, "Guard disabled"
        return self.rate_limiter.check_rate_limit(user_id, endpoint, tokens)

    def check_tool_permission(self, tool_name: str) -> tuple[Action, str]:
        if not self.enabled:
            return Action.ALLOW, "Guard disabled"
        return self.tool_permissions.check_permission(tool_name)

    def full_check(
        self,
        command: str | None = None,
        path: Path | str | None = None,
        operation: str = "read",
        tool_name: str | None = None,
        user_id: str = "",
        endpoint: str = "",
        tokens: int = 1,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {"overall_passed": True, "details": {}}
        if command is not None:
            safe, issues = self.is_command_safe(command)
            results["details"]["command_safe"] = safe
            results["details"]["command_issues"] = issues
            if not safe:
                results["overall_passed"] = False
        if path is not None:
            allowed, msg = self.is_path_allowed(path, operation)
            results["details"]["path_allowed"] = allowed
            results["details"]["path_message"] = msg
            if not allowed:
                results["overall_passed"] = False
        rate_ok, rate_msg = self.check_rate_limit(user_id, endpoint, tokens)
        results["details"]["rate_limit_ok"] = rate_ok
        results["details"]["rate_limit_msg"] = rate_msg
        if not rate_ok:
            results["overall_passed"] = False
        if tool_name is not None:
            action, perm_msg = self.check_tool_permission(tool_name)
            results["details"]["tool_permission"] = action.name
            results["details"]["tool_message"] = perm_msg
            if action != Action.ALLOW:
                results["overall_passed"] = False
        return results

    def get_guard_report(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "tool_permissions": {
                "allowed_count": len(self.tool_permissions.allowlist),
                "denied_count": len(self.tool_permissions.denylist),
                "audit_entries": len(self.tool_permissions.audit_log),
            },
            "rate_limiter": self.rate_limiter.get_stats(),
            "file_sandbox": {
                "allowed_roots": [str(r) for r in self.file_sandbox.allowed_roots],
                "read_only_count": len(self.file_sandbox.read_only_paths),
                "audit_entries": len(self.file_sandbox.audit_log),
            },
            "command_filter": {
                "danger_pattern_count": len(self.command_filter.danger_patterns),
                "audit_entries": len(self.command_filter.audit_log),
            },
        }
