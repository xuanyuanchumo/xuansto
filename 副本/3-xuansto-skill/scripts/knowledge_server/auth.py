import hmac
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Optional

logger = logging.getLogger("knowledge-server")


class ApiKeyAuth:
    def __init__(self, knowledge_root: Path):
        self._keys: dict[str, str] = {}
        self._load_keys(knowledge_root)

    def _load_keys(self, knowledge_root: Path):
        env_key = os.environ.get("KNOWLEDGE_API_KEY")
        if env_key:
            self._keys[env_key] = "admin"

        keys_file = knowledge_root / ".api_keys.json"
        if keys_file.exists():
            try:
                with open(keys_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for key, level in data.items():
                        self._keys[key] = level
            except Exception as e:
                logger.warning("operation=api_keys_load, status=failed, error=%s", e)

    def generate_key(self) -> str:
        return "xks-" + secrets.token_hex(32)

    def validate_key(self, key: str) -> bool:
        if not key:
            return False
        for stored_key in self._keys:
            if hmac.compare_digest(key, stored_key):
                return True
        return False

    def get_permission_level(self, key: str) -> Optional[str]:
        if not key:
            return None
        for stored_key, level in self._keys.items():
            if hmac.compare_digest(key, stored_key):
                return level
        return None

    @property
    def has_keys(self) -> bool:
        return len(self._keys) > 0

    def check_permission(self, key: str, required_levels: list[str]) -> bool:
        level = self.get_permission_level(key)
        if level is None:
            return False
        if level == "admin":
            return True
        if level == "read-write" and required_levels:
            return True
        if level == "read-only" and required_levels:
            return "read-only" in required_levels
        return level in required_levels
