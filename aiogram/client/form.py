from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from pydantic import BaseModel
from pydantic_core import to_json

from aiogram.client.default import DefaultBotProperties
from aiogram.default_annotations import get_default_prop_name, is_default_prop
from aiogram.types import InputFile

if TYPE_CHECKING:
    from aiogram import Bot


def extract_files_from_any(value: Any) -> Tuple[Any, Dict[str, InputFile]]:
    if isinstance(value, InputFile):
        token = secrets.token_urlsafe(10)
        return f"attach://{token}", {token: value}
    if isinstance(value, BaseModel):
        return extract_files_from_model(value)
    if isinstance(value, list):
        return extract_files_from_list(value)
    if isinstance(value, dict):
        return extract_files_from_dict(value)
    # TODO: add more collections if needed
    return value, {}


def extract_files_from_list(_list: List) -> Tuple[List, Dict[str, InputFile]]:
    modified_list = []
    list_files = {}
    for item in _list:
        modified_item, item_files = extract_files_from_any(item)
        modified_list.append(modified_item)
        list_files.update(item_files)
    return modified_list, list_files


def extract_files_from_dict(_dict: Dict) -> Tuple[Dict, Dict[str, InputFile]]:
    modified_dict = {}
    dict_files = {}
    for key, value in _dict.items():
        modified_value, value_files = extract_files_from_any(value)
        modified_dict[key] = modified_value
        dict_files.update(value_files)
    return modified_dict, dict_files


def extract_files_from_model(model: BaseModel) -> Tuple[BaseModel, Dict[str, InputFile]]:
    model_files = {}
    update = {}
    for field_name, field_value in model:
        modified_value, field_files = extract_files_from_any(field_value)
        if field_files:
            model_files.update(field_files)
            update[field_name] = modified_value
    modified_model = model.model_copy(update=update)
    return modified_model, model_files


def replace_default_props(model: BaseModel, *, props: DefaultBotProperties) -> BaseModel:
    if props.is_empty:
        return model
    update = {}
    for field_name, field_info in model.model_fields.items():
        field_value = getattr(model, field_name)
        if is_default_prop(field_info):
            default_name = get_default_prop_name(field_info)
            default_value = getattr(props, default_name)
            if field_value is None and default_value is not None:
                update[field_name] = default_value
        # TODO
    return model.model_copy(update=update)


def construct_form_data(model: BaseModel, bot: Bot) -> Tuple[Dict[str, str], Dict[str, InputFile]]:
    form_data = {}
    model, files = extract_files_from_model(model)
    model = replace_default_props(model, props=bot.default)
    for key, value in model.model_dump(exclude_none=True).items():
        form_data[key] = serialize_form_value(value)
    return form_data, files


def serialize_form_value(value: Any) -> str:
    """
    Prepare jsonable value to send
    """
    if isinstance(value, str):
        return value
    return to_json(value).decode()
