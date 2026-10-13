"""
Rich message content in the shape Telegram stores it.

A bot describes rich content with the ``InputRich*`` types, and Telegram
returns it as the ``Rich*`` types of the same name without the prefix.
Most fields keep their name and type across the two, so the conversion
here reflects over ``model_fields`` instead of listing block types: a
block type a future Bot API version adds converts with no change here.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import UnionType
from typing import Annotated, Any, Union, cast, get_args, get_origin

from pydantic import BaseModel
from typing_extensions import TypeAliasType

import aiogram.types as api_types
from aiogram.types import InputMedia, InputRichMessage, RichMessage

from .synthesis import SynthesisContext, nonempty, synthesize

_INPUT_PREFIX = "Input"

#: What a field the stored shape requires, but the request left unset,
#: gets. Telegram does not document its own fill-ins; zero values are
#: valid in every range the Bot API documents for these fields.
_ZERO_VALUES: dict[type, Any] = {int: 0, float: 0.0, str: "", bool: False}


def counterpart(model: type[BaseModel]) -> type[BaseModel] | None:
    """The stored ``Rich*`` type an ``InputRich*`` type converts to."""
    name = model.__name__
    if not name.startswith(_INPUT_PREFIX + "Rich"):
        return None
    target = getattr(api_types, name.removeprefix(_INPUT_PREFIX), None)
    if isinstance(target, type) and issubclass(target, BaseModel):
        return target
    return None


def models_in(annotation: Any) -> Iterator[type[BaseModel]]:
    """Every model class an annotation can hold, through unions and lists."""
    if isinstance(annotation, TypeAliasType):
        yield from models_in(annotation.__value__)
        return
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            yield annotation
        return
    origin = get_origin(annotation)
    if origin is Annotated:
        yield from models_in(get_args(annotation)[0])
        return
    for argument in get_args(annotation):
        yield from models_in(argument)


def materialize_rich_message(
    value: InputRichMessage,
    context: SynthesisContext,
) -> RichMessage:
    """Convert what a request carried into the rich content stored."""
    return cast(RichMessage, _convert_model(value, context))


def _convert_model(value: BaseModel, context: SynthesisContext) -> BaseModel:
    source_type = type(value)
    target_type = counterpart(source_type)
    if target_type is None:  # pragma: no cover - guarded by a test
        msg = f"{source_type.__name__} has no stored counterpart"
        raise TypeError(msg)
    values: dict[str, Any] = {}
    for name, info in target_type.model_fields.items():
        if name == "type":
            # The input and stored discriminators are different enums,
            # so the target keeps its own default.
            continue
        source_info = source_type.model_fields.get(name)
        raw = getattr(value, name, None) if source_info is not None else None
        if raw is not None:
            if source_info is not None and source_info.annotation == info.annotation:
                values[name] = raw
            else:
                values[name] = _convert_value(raw, info.annotation, name, context)
            continue
        carried = _media_attribute(value, name)
        if carried is not None:
            values[name] = carried
        elif info.is_required():
            values[name] = _zero_value(info.annotation, name, context)
    return target_type.model_validate(values)


def _convert_value(
    raw: Any,
    annotation: Any,
    name: str,
    context: SynthesisContext,
) -> Any:
    if isinstance(raw, list):
        item = _list_item(annotation)
        return [_convert_value(entry, item, name, context) for entry in raw]
    if isinstance(raw, InputMedia):
        return nonempty(annotation, context, name=name)
    if isinstance(raw, BaseModel) and counterpart(type(raw)) is not None:
        return _convert_model(raw, context)
    return raw


def _media_attribute(value: BaseModel, name: str) -> Any:
    """
    A media attribute the stored block carries itself.

    ``has_spoiler`` sits on the input media but on the stored block, so
    it is read off whichever input media field the block has.
    """
    for field in type(value).model_fields:
        media = getattr(value, field, None)
        if isinstance(media, InputMedia):
            attribute = getattr(media, name, None)
            if attribute is not None:
                return attribute
    return None


def _zero_value(annotation: Any, name: str, context: SynthesisContext) -> Any:
    if annotation in _ZERO_VALUES:
        return _ZERO_VALUES[annotation]
    if get_origin(annotation) is list:
        return []
    return synthesize(annotation, context, name=name)


def _list_item(annotation: Any) -> Any:
    if get_origin(annotation) in {UnionType, Union}:
        for member in get_args(annotation):
            if get_origin(member) is list:
                return get_args(member)[0]
    if get_origin(annotation) is list:
        return get_args(annotation)[0]
    return annotation
