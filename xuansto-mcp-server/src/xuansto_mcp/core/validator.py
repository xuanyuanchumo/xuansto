from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ValidationError as PydanticValidationError
from .errors import make_error_response, ERR_VALIDATION


def validate_input(model_class: type[BaseModel], **kwargs: Any) -> tuple[BaseModel | None, dict[str, Any] | None]:
    try:
        instance = model_class(**kwargs)
        return instance, None
    except PydanticValidationError as e:
        return None, make_error_response(e, error_code=ERR_VALIDATION)
