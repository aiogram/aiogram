from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.methods import TelegramMethod
from aiogram.types import Message

from .blueprint import Blueprint, default_blueprint
from .environment import BotTestEnvironment
from .world import ChatState

__all__ = (
    "bot_blueprint",
    "bot_chat",
    "bot_dispatcher",
    "bot_env",
    "bot_user",
    "pytest_assertrepr_compare",
)


@pytest.fixture
def bot_blueprint() -> Blueprint:
    """
    World declaration. Override this fixture — at any scope — to describe your own
    chats, users and memberships; environments are always built fresh per test.
    """
    return default_blueprint()


@pytest.fixture
def bot_dispatcher() -> Dispatcher:
    """Override this fixture to return the dispatcher with your real routers."""
    return Dispatcher()


@pytest.fixture
def bot_env(
    bot_blueprint: Blueprint,
    bot_dispatcher: Dispatcher,
) -> Iterator[BotTestEnvironment]:
    """An isolated fake Telegram world for exactly one test."""
    environment = BotTestEnvironment(blueprint=bot_blueprint, dispatcher=bot_dispatcher)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def bot_chat(bot_env: BotTestEnvironment) -> ChatState:
    """The first chat declared by the blueprint."""
    return bot_env.chat(bot_env.blueprint.chats[0].id)


@pytest.fixture
def bot_user(bot_env: BotTestEnvironment) -> Any:
    """An actor for the first user declared by the blueprint, bound to the first chat."""
    actor = bot_env.user(bot_env.blueprint.users[0].id)
    if bot_env.blueprint.chats:
        return actor.in_(bot_env.blueprint.chats[0].id)
    return actor


def pytest_assertrepr_compare(op: str, left: object, right: object) -> list[str] | None:
    """Make failures about world state and recorded calls readable."""
    if op != "==":
        return None
    if isinstance(left, ChatState) or isinstance(right, ChatState):
        chat = left if isinstance(left, ChatState) else right
        assert isinstance(chat, ChatState)
        return [
            f"chat {chat.id} ({chat.type}) contains {len(chat.messages)} message(s):",
            *[f"  #{item.message_id}: {_describe_message(item)}" for item in chat.messages],
        ]
    if isinstance(left, TelegramMethod) and isinstance(right, TelegramMethod):
        return [
            f"{type(left).__name__} != {type(right).__name__}"
            if type(left) is not type(right)
            else f"{type(left).__name__} fields differ:",
            *_describe_diff(left, right),
        ]
    return None


def _describe_message(message: Message) -> str:
    body = message.text or message.caption or message.content_type
    markup = " [keyboard]" if message.reply_markup is not None else ""
    return f"{body!r}{markup}"


def _describe_diff(left: TelegramMethod[Any], right: TelegramMethod[Any]) -> list[str]:
    lines: list[str] = []
    for name in type(left).model_fields:
        left_value = getattr(left, name, None)
        right_value = getattr(right, name, None)
        if left_value != right_value:
            lines.append(f"  {name}: {left_value!r} != {right_value!r}")
    return lines
