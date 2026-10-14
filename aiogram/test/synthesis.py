from __future__ import annotations

import datetime
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import cache
from types import UnionType
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing_extensions import TypeAliasType

import aiogram.enums as api_enums
from aiogram.types import BufferedInputFile, Chat, User

from .world import BASE_DATE


class SynthesisError(RuntimeError):
    """Raised when no schema-valid result can be built for a Bot API return type."""


@dataclass
class SynthesisContext:
    """Values the synthesizer seeds into results so they belong to the test world."""

    chat: Chat | None = None
    user: User | None = None
    date: datetime.datetime = BASE_DATE
    counter: int = 0
    #: Numbers a synthesized file, so files stay apart across calls;
    #: the context's own counter when there is no world to ask.
    file_numbers: Callable[[], int] | None = None
    #: The world's file store, which uploads register their bytes in.
    files: dict[str, bytes] | None = None

    def next_int(self) -> int:
        self.counter += 1
        return self.counter

    def next_file_number(self) -> int:
        if self.file_numbers is not None:
            return self.file_numbers()
        return self.next_int()


def passed_file_id(uploaded: Any) -> str | None:
    """
    The file id a request passed as its media, if it passed one.

    A string is a file id, or an HTTP URL Telegram downloads, which
    gets an id of its own.
    """
    if isinstance(uploaded, str) and not uploaded.startswith(("http://", "https://")):
        return uploaded
    return None


def with_passed_file(payload: Any, uploaded: Any, context: SynthesisContext) -> Any:
    """
    ``payload``, holding the file the request passed as ``uploaded``.

    A passed file id replaces the synthesized one. The bytes of a
    :class:`~aiogram.types.input_file.BufferedInputFile` are stored
    under the synthesized id; no other upload is read, since a test
    environment must not touch the disk or the network.
    """
    items = payload if isinstance(payload, list) else [payload]
    file_id = passed_file_id(uploaded)
    if file_id is not None:
        items = [
            item.model_copy(update={"file_id": file_id}) if hasattr(item, "file_id") else item
            for item in items
        ]
    elif isinstance(uploaded, BufferedInputFile) and context.files is not None:
        for item in items:
            if hasattr(item, "file_id"):
                context.files[item.file_id] = uploaded.data
    return items if isinstance(payload, list) else items[0]


@cache
def _required_fields(model: type[BaseModel]) -> tuple[tuple[str, FieldInfo], ...]:
    return tuple((name, info) for name, info in model.model_fields.items() if info.is_required())


def _union_members(annotation: Any) -> tuple[Any, ...]:
    return tuple(arg for arg in get_args(annotation) if arg is not type(None))


def annotation_accepts(annotation: Any, target: type) -> bool:
    if isinstance(annotation, TypeAliasType):
        return annotation_accepts(annotation.__value__, target)
    if get_origin(annotation) is Annotated:
        return annotation_accepts(get_args(annotation)[0], target)
    if isinstance(annotation, type):
        return issubclass(annotation, target)
    if get_origin(annotation) in {UnionType, Union}:
        return any(annotation_accepts(member, target) for member in _union_members(annotation))
    return False


def without_none(annotation: Any) -> Any:
    """``X`` out of ``X | None``; any other annotation as it is."""
    if get_origin(annotation) in {UnionType, Union}:
        return next(
            (arg for arg in get_args(annotation) if arg is not type(None)),
            annotation,
        )
    return annotation


def list_item(annotation: Any) -> Any | None:
    """The item type of a list annotation, optional or not."""
    members = without_none(annotation)
    if get_origin(members) is list:
        return get_args(members)[0]
    return None


def nonempty(annotation: Any, context: SynthesisContext, *, name: str) -> Any:
    """Synthesize a value, giving a list annotation one element."""
    item = list_item(annotation)
    if item is not None:
        return [synthesize(item, context, name=name)]
    return synthesize(without_none(annotation), context, name=name)


def synthesize(
    annotation: Any,
    context: SynthesisContext,
    *,
    name: str = "result",
    path: str = "",
    stack: tuple[type, ...] = (),
) -> Any:
    """Build a schema-valid value for ``annotation`` using only pydantic metadata."""
    where = f"{path}.{name}" if path else name
    origin = get_origin(annotation)

    if origin is Literal:
        return get_args(annotation)[0]
    if origin in {UnionType, Union}:
        # A union always keeps at least one non-None member — `Optional[None]` collapses
        # to `None` before it reaches here.
        return synthesize(
            _union_members(annotation)[0],
            context,
            name=name,
            path=path,
            stack=stack,
        )
    if origin in {list, set, frozenset, tuple}:
        return []
    if origin is dict:
        return {}
    if annotation is Any:
        return None

    if not isinstance(annotation, type):
        msg = (
            f"Cannot synthesize a value for {where!r} of type {annotation!r}. "
            f"Register an explicit result for this method with `env.on(...).returns(...)`."
        )
        raise SynthesisError(msg)

    if issubclass(annotation, Enum):
        return next(iter(annotation)).value
    if issubclass(annotation, bool):
        # The absent-flag reading every optional Bot API flag has.
        return False
    if issubclass(annotation, int):
        # Synthesized lists are empty, so whatever they count is zero.
        return 0 if name in _LIST_COUNTS else context.next_int()
    if issubclass(annotation, float):
        return float(context.next_int())
    if issubclass(annotation, datetime.datetime):
        return context.date
    if issubclass(annotation, datetime.timedelta):
        return datetime.timedelta(0)
    if issubclass(annotation, str):
        enumerated = _enumerated(stack[-1], name) if stack else None
        return name if enumerated is None else enumerated
    if issubclass(annotation, bytes):
        return b""
    if issubclass(annotation, BaseModel):
        return _synthesize_model(annotation, context, path=where, stack=stack)

    msg = (
        f"Cannot synthesize a value for {where!r} of type {annotation.__name__!r}. "
        f"Register an explicit result for this method with `env.on(...).returns(...)`."
    )
    raise SynthesisError(msg)


def _synthesize_model(
    model: type[BaseModel],
    context: SynthesisContext,
    *,
    path: str,
    stack: tuple[type, ...],
) -> BaseModel:
    if model in stack:
        chain = " -> ".join(item.__name__ for item in (*stack, model))
        msg = (
            f"Cannot synthesize {path!r}: recursive required field chain {chain}. "
            f"Register an explicit result for this method with `env.on(...).returns(...)`."
        )
        raise SynthesisError(msg)

    values: dict[str, Any] = {}
    if {"file_id", "file_unique_id"} <= model.model_fields.keys():
        number = context.next_file_number()
        values["file_id"] = f"file-{number}"
        values["file_unique_id"] = f"unique-{number}"
    for name, info in _required_fields(model):
        if name in values:
            continue
        seeded = _seed(name, info, context)
        if seeded is not None:
            values[name] = seeded
            continue
        values[name] = synthesize(
            info.annotation,
            context,
            name=name,
            path=path,
            stack=(*stack, model),
        )
    return model(**values)


#: The counts of what a list holds. Synthesized lists are empty, so
#: these are zero; other counts, a price or a winner count, are not.
_LIST_COUNTS = frozenset(
    {"total_count", "voter_count", "total_voter_count", "pending_update_count"},
)

#: Enum members valid only in a field other than the one the enum
#: is named after: ``sender`` is an inline query's ``chat_type``,
#: never a ``Chat.type``.
_ONLY_ELSEWHERE: frozenset[Enum] = frozenset({api_enums.ChatType.SENDER})


def _enumerated(model: type, name: str) -> str | None:
    """
    The first value aiogram enumerates for ``model.name``, if any.

    aiogram names such an enum after the model and the field, as
    ``StickerType`` for ``Sticker.type``, so the values follow the
    Bot API with no list kept here.
    """
    camel = "".join(part.capitalize() for part in name.split("_"))
    enum = getattr(api_enums, f"{model.__name__}{camel}", None)
    if isinstance(enum, type) and issubclass(enum, Enum):
        member = next(m for m in enum if m not in _ONLY_ELSEWHERE)
        return str(member.value)
    return None


def _seed(name: str, info: FieldInfo, context: SynthesisContext) -> Any:
    """Fill fields whose meaning is unambiguous from the environment itself."""
    if context.chat is not None and name == "chat" and annotation_accepts(info.annotation, Chat):
        return context.chat
    if (
        context.user is not None
        and name in {"from_user", "user"}
        and annotation_accepts(info.annotation, User)
    ):
        return context.user
    return None


def synthesize_result(returning: Any, context: SynthesisContext) -> Any:
    """Build a result for a method's ``__returning__`` annotation."""
    if returning is bool:
        # A method returning a boolean returns True on success.
        return True
    return synthesize(returning, context)
