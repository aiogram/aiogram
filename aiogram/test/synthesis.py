from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum
from functools import cache
from types import UnionType
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from aiogram.types import Chat, User

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

    def next_int(self) -> int:
        self.counter += 1
        return self.counter


@cache
def _required_fields(model: type[BaseModel]) -> tuple[tuple[str, FieldInfo], ...]:
    return tuple((name, info) for name, info in model.model_fields.items() if info.is_required())


def _union_members(annotation: Any) -> tuple[Any, ...]:
    return tuple(arg for arg in get_args(annotation) if arg is not type(None))


def annotation_accepts(annotation: Any, target: type) -> bool:
    if isinstance(annotation, type):
        return issubclass(annotation, target)
    if get_origin(annotation) in {UnionType, Union}:
        return any(annotation_accepts(member, target) for member in _union_members(annotation))
    return False


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
        return True
    if issubclass(annotation, int):
        return context.next_int()
    if issubclass(annotation, float):
        return float(context.next_int())
    if issubclass(annotation, datetime.datetime):
        return context.date
    if issubclass(annotation, datetime.timedelta):
        return datetime.timedelta(0)
    if issubclass(annotation, str):
        return name
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
    for name, info in _required_fields(model):
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
    return synthesize(returning, context)
