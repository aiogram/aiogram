from __future__ import annotations

import secrets
import typing
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel
from pydantic_core import to_json

from aiogram.types import InputFile

M = typing.TypeVar("M", bound=BaseModel)


def _extract_files(value: Any) -> Tuple[Any, Dict[str, InputFile]]:
    files = {}

    # Handle input file
    if isinstance(value, InputFile):
        token = secrets.token_urlsafe(10)
        files[token] = value
        return f"attach://{token}", files

    # Handle nested models
    if isinstance(value, BaseModel):
        modified_nested_model, nested_files = extract_files(value, files)
        files.update(nested_files)
        return modified_nested_model, files

    return value, files


def extract_files(
    model: M,
    files: Optional[Dict[str, InputFile]] = None,
) -> Tuple[M, Dict[str, InputFile]]:
    if files is None:
        files = {}
    update = {}

    for field_name, field_value in model:
        modified_field_value, nested_files = _extract_files(field_value)
        update[field_name] = modified_field_value
        files.update(nested_files)

        # Handle nested models inside of lists (media groups)
        if isinstance(field_value, list):
            update[field_name] = []
            for item in field_value:
                modified_item, nested_item_files = _extract_files(item)
                update[field_name].append(modified_item)
                files.update(nested_item_files)
            continue

    modified_model = model.model_copy(update=update)
    return modified_model, files


def form_serialize(value: Any) -> str:
    """
    Prepare jsonable value to send
    """
    if isinstance(value, str):
        return value
    return to_json(value).decode()
