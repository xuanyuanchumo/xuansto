from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_CRYPTO_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_AVAILABLE = True
except ImportError:
    pass

_ENCRYPTION_KEY_ENV = "XUANSTO_ENCRYPTION_KEY"
_NONCE_SIZE = 12
_KEY_SIZE = 32
_BACKUP_KEY_FILENAME = ".backup_key"


def _get_backup_key_path() -> Path:
    try:
        from .config import KNOWLEDGE_DIR
        return KNOWLEDGE_DIR / _BACKUP_KEY_FILENAME
    except Exception:
        return Path(".knowledge") / _BACKUP_KEY_FILENAME


def _auto_generate_key() -> bytes | None:
    if not _CRYPTO_AVAILABLE:
        return None
    key_path = _get_backup_key_path()
    if key_path.exists():
        try:
            key_hex = key_path.read_text(encoding="utf-8").strip()
            key = bytes.fromhex(key_hex)
            if len(key) == _KEY_SIZE:
                return key
        except (ValueError, OSError):
            pass
    try:
        key = os.urandom(_KEY_SIZE)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(key.hex(), encoding="utf-8")
        return key
    except OSError:
        return None


def _get_key() -> bytes | None:
    key_hex = os.environ.get(_ENCRYPTION_KEY_ENV)
    if key_hex:
        try:
            key = bytes.fromhex(key_hex)
            if len(key) == _KEY_SIZE:
                return key
        except ValueError:
            pass
    return _auto_generate_key()


def is_encryption_available() -> bool:
    return _CRYPTO_AVAILABLE


def encrypt_data(data: bytes) -> bytes:
    key = _get_key()
    if key is None or not _CRYPTO_AVAILABLE:
        return data
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_data(data: bytes) -> bytes:
    key = _get_key()
    if key is None or not _CRYPTO_AVAILABLE:
        return data
    if len(data) < _NONCE_SIZE:
        return data
    nonce = data[:_NONCE_SIZE]
    ciphertext = data[_NONCE_SIZE:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def mark_encrypted(metadata: dict[str, Any]) -> dict[str, Any]:
    metadata["encrypted"] = True
    metadata["encryption_algorithm"] = "AES-256-GCM"
    return metadata


def is_encrypted(metadata: dict[str, Any]) -> bool:
    return metadata.get("encrypted", False)
