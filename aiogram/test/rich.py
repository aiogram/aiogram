"""
Rich message content in the shape Telegram stores it.

A bot describes rich content with the ``InputRich*`` types, and Telegram
returns it as the ``Rich*`` types of the same name without the prefix.
Most fields keep their name and type across the two, so the conversion
here reflects over ``model_fields`` instead of listing block types: a
block type a future Bot API version adds converts with no change here.
"""

from __future__ import annotations

from typing import Any, cast, get_origin

from pydantic import BaseModel

import aiogram.types as api_types
from aiogram.types import InputRichMessage, RichMessage

from .synthesis import (
    SynthesisContext,
    annotation_accepts,
    list_item,
    nonempty,
    synthesize,
)

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
        # Only a field the input block lacks is read off its media: one
        # it has, such as `caption`, has its own type on the block.
        carried = _media_attribute(value, target_type, name) if source_info is None else None
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
        item = list_item(annotation)
        entry_type = annotation if item is None else item
        return [_convert_value(entry, entry_type, name, context) for entry in raw]
    if _is_media(raw, annotation):
        return nonempty(annotation, context, name=name)
    if isinstance(raw, BaseModel) and counterpart(type(raw)) is not None:
        return _convert_model(raw, context)
    return raw


def _is_media(raw: Any, annotation: Any) -> bool:
    """
    Whether ``raw`` is media the stored shape holds as a file instead.

    A model with no stored counterpart that the stored field does not
    accept as it is can only be media: ``InputMediaPhoto`` becomes a
    list of ``PhotoSize``, ``InputMediaVoiceNote`` a ``Voice``. Not
    every input media subclasses ``InputMedia``, so this does not ask.
    """
    return (
        isinstance(raw, BaseModel)
        and counterpart(type(raw)) is None
        and not annotation_accepts(annotation, type(raw))
    )


def _media_attribute(value: BaseModel, target_type: type[BaseModel], name: str) -> Any:
    """
    A media attribute the stored block carries itself.

    ``has_spoiler`` sits on the input media but on the stored block, so
    it is read off whichever input media field the block has.
    """
    for field in type(value).model_fields:
        media = getattr(value, field, None)
        stored = target_type.model_fields.get(field)
        if stored is not None and _is_media(media, stored.annotation):
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
