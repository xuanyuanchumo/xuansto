import logging
import re
import threading
import time

logger = logging.getLogger("knowledge-server")


class SensitiveContentFilter:
    PATTERNS = [
        (re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE), 'API Key'),
        (re.compile(r'api_key\s*=\s*["\']?[^\s"\']+', re.IGNORECASE), 'API Key'),
        (re.compile(r'key\s*=\s*["\']?[^\s"\']{16,}', re.IGNORECASE), 'API Key'),
        (re.compile(r'token\s*=\s*["\']?[^\s"\']+', re.IGNORECASE), 'Token'),
        (re.compile(r'password\s*=\s*["\']?[^\s"\']+', re.IGNORECASE), 'Password'),
        (re.compile(r'passwd\s*=\s*["\']?[^\s"\']+', re.IGNORECASE), 'Password'),
        (re.compile(r'pwd\s*=\s*["\']?[^\s"\']+', re.IGNORECASE), 'Password'),
        (re.compile(r'Bearer\s+[^\s]+', re.IGNORECASE), 'Bearer Token'),
        (re.compile(r'jwt\s+[^\s]+', re.IGNORECASE), 'JWT Token'),
        (re.compile(r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', re.IGNORECASE), 'JWT Token'),
    ]

    @classmethod
    def scan(cls, content: str) -> list[dict]:
        findings = []
        for pattern, category in cls.PATTERNS:
            matches = pattern.findall(content)
            if matches:
                findings.append({
                    "category": category,
                    "pattern": pattern.pattern,
                    "count": len(matches),
                })
        return findings

    @classmethod
    def check(cls, content: str) -> tuple[bool, list[dict]]:
        findings = cls.scan(content)
        return len(findings) > 0, findings


class InputValidator:
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(union\s+select|select\s+.+\s+from|insert\s+into|delete\s+from|drop\s+table|alter\s+table|exec\s*\(|execute\s*\(|xp_cmdshell|sp_executesql)\b)", re.IGNORECASE),
        re.compile(r"(-{2}|;|/\*|\*/)", re.IGNORECASE),
        re.compile(r"('\s*(or|and)\s+['\d])", re.IGNORECASE),
        re.compile(r"(\b(waitfor\s+delay|benchmark\s*\(|sleep\s*\()\b)", re.IGNORECASE),
    ]

    PATH_TRAVERSAL_PATTERN = re.compile(r"(\.\.[/\\]|\.\.%2[fF]|%2[eE]%2[eE][/\\])")

    XSS_PATTERN = re.compile(r"<\s*script[^>]*>|<\s*/\s*script\s*>|javascript\s*:|on\w+\s*=", re.IGNORECASE)

    @classmethod
    def validate_sql_injection(cls, value: str) -> tuple[bool, str]:
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                return False, "Potential SQL injection detected"
        return True, ""

    @classmethod
    def validate_path_traversal(cls, value: str) -> tuple[bool, str]:
        if cls.PATH_TRAVERSAL_PATTERN.search(value):
            return False, "Path traversal attempt detected"
        return True, ""

    @classmethod
    def validate_xss(cls, value: str) -> tuple[bool, str]:
        if cls.XSS_PATTERN.search(value):
            return False, "XSS content detected"
        return True, ""

    @classmethod
    def validate_all(cls, **kwargs) -> list[str]:
        errors = []
        for key, value in kwargs.items():
            if not isinstance(value, str) or not value:
                continue
            ok, msg = cls.validate_sql_injection(value)
            if not ok:
                errors.append(f"{key}: {msg}")
            ok, msg = cls.validate_path_traversal(value)
            if not ok:
                errors.append(f"{key}: {msg}")
            ok, msg = cls.validate_xss(value)
            if not ok:
                errors.append(f"{key}: {msg}")
        return errors


class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        window_start = now - self._window_seconds

        with self._lock:
            if client_ip not in self._requests:
                self._requests[client_ip] = []

            self._requests[client_ip] = [
                ts for ts in self._requests[client_ip] if ts > window_start
            ]

            if len(self._requests[client_ip]) >= self._max_requests:
                oldest = self._requests[client_ip][0]
                retry_after = int(oldest + self._window_seconds - now) + 1
                return False, max(retry_after, 1)

            self._requests[client_ip].append(now)
            return True, 0

    def cleanup(self):
        now = time.time()
        window_start = now - self._window_seconds
        with self._lock:
            expired_ips = []
            for ip, timestamps in self._requests.items():
                self._requests[ip] = [ts for ts in timestamps if ts > window_start]
                if not self._requests[ip]:
                    expired_ips.append(ip)
            for ip in expired_ips:
                del self._requests[ip]
