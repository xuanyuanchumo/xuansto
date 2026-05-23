from __future__ import annotations

from pathlib import Path
from typing import Any
from pydantic import BaseModel, ValidationError as PydanticValidationError
from .errors import make_error_response, ERR_VALIDATION


def validate_path_safety(
    path_component: str,
    allowed_base_dirs: list[Path] | None = None,
) -> tuple[Path | None, str | None]:
    if "\x00" in path_component:
        return None, f"Path contains null byte: {path_component!r}"
    if ".." in Path(path_component).parts:
        return None, f"Path traversal detected (..): {path_component!r}"
    if Path(path_component).is_absolute():
        return None, f"Absolute path not allowed: {path_component!r}"
    if "/" in path_component or "\\" in path_component:
        resolved = Path(path_component)
        if ".." in resolved.parts:
            return None, f"Path traversal detected (..): {path_component!r}"
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
