from __future__ import annotations

import os
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


def _get_key() -> bytes | None:
    key_hex = os.environ.get(_ENCRYPTION_KEY_ENV)
    if not key_hex:
        return None
    try:
        key = bytes.fromhex(key_hex)
        if len(key) != _KEY_SIZE:
            return None
        return key
    except ValueError:
        return None


def is_encryption_available() -> bool:
    if not _CRYPTO_AVAILABLE:
        return False
    return _get_key() is not None


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
