from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.methods import TelegramMethod
from aiogram.types import Message, TelegramObject

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
    if _differ_only_in_binding(left, right):
        assert isinstance(left, TelegramObject)
        assert isinstance(right, TelegramObject)
        return [
            f"two {type(left).__name__} objects that differ only in the bot they are bound to:",
            f"  left is {_describe_binding(left)}, right is {_describe_binding(right)}",
            "Pydantic compares private attributes, and `_bot` is one of them, while the",
            "repr hides it — which is why these two print identically yet are not equal.",
            "Objects the fake world hands out are mounted to a bot the way parsed ones",
            "are; an object built inside the test is not. Compare the payload instead:",
            "  assert left.model_dump() == right.model_dump()",
        ]
    return None


def _differ_only_in_binding(left: object, right: object) -> bool:
    """Same type, same payload, different bot — the only thing left to disagree about."""
    if not isinstance(left, TelegramObject) or not isinstance(right, TelegramObject):
        return False
    if type(left) is not type(right) or left.bot is right.bot:
        return False
    return left.model_dump() == right.model_dump()


def _describe_binding(item: TelegramObject) -> str:
    bot = item.bot
    return "not mounted to any bot" if bot is None else f"mounted to bot id={bot.id}"


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
