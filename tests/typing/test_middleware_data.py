# Typed DI (D31): what mypy sees through the middleware data TypedDicts (E-20).
from collections.abc import Awaitable, Callable
from typing import Any, Unpack, assert_type

from aiogram import Bot, Router
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.dispatcher.middlewares.data import (
    MiddlewareData,
    OuterData,
    RouterOuterData,
)
from aiogram.dispatcher.middlewares.user_context import EventContext
from aiogram.types import Message, Update
from aiogram.utils.i18n import I18n


class AppData(MiddlewareData):
    db: str


async def handler(message: Message, **kw: Unpack[AppData]) -> None:
    assert_type(kw["bot"], Bot)
    assert_type(kw["db"], str)
    assert_type(kw["handler"], HandlerObject)
    assert_type(kw["event_router"], Router)
    assert_type(kw["event_update"], Update)
    assert_type(kw["event_context"], EventContext)
    assert_type(kw.get("bots"), tuple[Bot, ...] | None)
    assert_type(kw.get("i18n"), I18n | None)
    kw["nope"]  # type: ignore[typeddict-item]


async def outer(
    handler: Callable[[Update, OuterData], Awaitable[Any]],
    event: Update,
    data: OuterData,
) -> Any:
    assert_type(data["bot"], Bot)
    data["handler"]  # type: ignore[typeddict-item]
    data["event_router"]  # type: ignore[typeddict-item]
    data["event_update"]  # type: ignore[typeddict-item]
    data["state"]  # type: ignore[typeddict-item]
    return await handler(event, data)


def router_outer(data: RouterOuterData) -> None:
    assert_type(data["event_router"], Router)
    data["handler"]  # type: ignore[typeddict-item]


Router().message.register(handler)
