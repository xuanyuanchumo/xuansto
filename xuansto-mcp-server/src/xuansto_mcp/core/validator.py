from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ValidationError as PydanticValidationError
from .errors import make_error_response, ERR_VALIDATION

NAME_WHITELIST_PATTERN = re.compile(r'^[a-zA-Z0-9_\-./]+$')


def validate_name_parameter(name: str) -> tuple[bool, str | None]:
    if not name:
        return False, "Name parameter must not be empty"
    if "\x00" in name:
        return False, f"Name contains null byte: {name!r}"
    if ".." in name:
        return False, f"Path traversal detected (..): {name!r}"
    if Path(name).is_absolute():
        return False, f"Absolute path not allowed in name: {name!r}"
    if not NAME_WHITELIST_PATTERN.match(name):
        return False, f"Name contains invalid characters: {name!r}"
    return True, None


def validate_path_safety(
    path_component: str,
    allowed_base_dirs: list[Path] | None = None,
    allow_absolute: bool = False,
) -> tuple[Path | None, str | None]:
    if "\x00" in path_component:
        return None, f"Path contains null byte: {path_component!r}"
    resolved = Path(path_component)
    if ".." in resolved.parts:
        return None, f"Path traversal detected (..): {path_component!r}"
    if resolved.is_absolute() and not allow_absolute:
        return None, f"Absolute path not allowed: {path_component!r}"
    if resolved.is_absolute() and allow_absolute:
        try:
            real_resolved = resolved.resolve()
            if ".." in real_resolved.parts:
                return None, f"Path traversal detected after resolve (..): {path_component!r}"
        except (OSError, ValueError):
            return None, f"Invalid path: {path_component!r}"
    if allowed_base_dirs:
        candidate = None
        for base_dir in allowed_base_dirs:
            candidate = base_dir / path_component
            try:
                resolved_candidate = candidate.resolve()
                resolved_base = base_dir.resolve()
                if not resolved_candidate.is_relative_to(resolved_base):
                    return None, f"Path escapes allowed directory: {path_component!r}"
            except (OSError, ValueError):
                return None, f"Invalid path: {path_component!r}"
        return candidate, None
    return Path(path_component), None


def validate_input(model_class: type[BaseModel], **kwargs: Any) -> tuple[BaseModel | None, dict[str, Any] | None]:
    try:
        instance = model_class(**kwargs)
        return instance, None
    except PydanticValidationError as e:
        return None, make_error_response(e, error_code=ERR_VALIDATION)
