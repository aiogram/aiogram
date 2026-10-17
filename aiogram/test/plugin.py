from __future__ import annotations

import datetime
from collections.abc import Generator, Iterator
from typing import Any

import pytest

from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.methods import TelegramMethod
from aiogram.types import Message, TelegramObject

from .blueprint import Blueprint, default_blueprint
from .environment import BotTestEnvironment
from .flood import RateLimits
from .waiting import DEFAULT_WAIT_TIMEOUT
from .world import ChatState

__all__ = (
    "bot_blueprint",
    "bot_chat",
    "bot_dispatcher",
    "bot_env",
    "bot_env_assert_updates_handled",
    "bot_env_wait_timeout",
    "bot_user",
    "pytest_assertrepr_compare",
    "pytest_runtest_call",
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
def bot_env_wait_timeout() -> float:
    """
    Override this fixture — at any scope — to change how long every wait in ``bot_env``
    runs by default, without copying the whole fixture just to pass
    ``default_wait_timeout=...`` to :class:`~aiogram.test.BotTestEnvironment` by hand.

    Mirrors ``bot_blueprint`` and ``bot_dispatcher``: a value fixture the plugin's own
    fixture reads, rather than a setting only reachable by rebuilding the environment
    fixture from scratch. An explicit ``timeout=`` on a single wait still wins over it.
    """
    return DEFAULT_WAIT_TIMEOUT


@pytest.fixture
def bot_env_clock_start() -> datetime.datetime | None:
    """
    Override this fixture to start ``bot_env``'s clock at a moment.

    ``None``, the default, starts it at the real time. Returning
    ``BASE_DATE`` gives dates that are the same on every run.
    """
    return None


@pytest.fixture
def bot_env_enforce_bot_rights() -> bool:
    """
    Override this fixture to stop checking the bot's rights.

    ``True``, the default, refuses the bot's calls its standing in a
    chat does not allow. Return ``False`` while migrating a suite
    written against the permissive fake.
    """
    return True


@pytest.fixture
def bot_env_rate_limits() -> RateLimits | None:
    """
    Override this fixture to hold ``bot_env`` to flood limits.

    ``None``, the default, models none. Return ``RateLimits()`` for
    Telegram's guidance, or limits of your own.
    """
    return None


@pytest.fixture
def bot_env_deliver_bot_service_messages() -> bool:
    """
    Override this fixture to withhold other bots' service messages.

    ``True``, the default, delivers a service message another bot
    causes. Telegram does not document either way; return ``False``
    to test a bot that never sees them.
    """
    return True


@pytest.fixture
def bot_env_assert_updates_handled() -> bool:
    """
    Override this fixture to check every update after each test.

    ``False``, the default, checks nothing. With ``True``, a test
    that passes then fails if an update it fed went unhandled or
    raised, as
    :meth:`~aiogram.test.BotTestEnvironment.assert_updates_handled`
    says, unless the test called ``assert_unhandled()`` for it.
    """
    return False


@pytest.fixture
def bot_env(
    bot_blueprint: Blueprint,
    bot_dispatcher: Dispatcher,
    bot_env_wait_timeout: float,
    bot_env_clock_start: datetime.datetime | None,
    bot_env_enforce_bot_rights: bool,
    bot_env_rate_limits: RateLimits | None,
    bot_env_assert_updates_handled: bool,
    bot_env_deliver_bot_service_messages: bool,
) -> Iterator[BotTestEnvironment]:
    """An isolated fake Telegram world for exactly one test."""
    environment = BotTestEnvironment(
        blueprint=bot_blueprint,
        dispatcher=bot_dispatcher,
        default_wait_timeout=bot_env_wait_timeout,
        clock_start=bot_env_clock_start,
        enforce_bot_rights=bot_env_enforce_bot_rights,
        rate_limits=bot_env_rate_limits,
        deliver_bot_service_messages=bot_env_deliver_bot_service_messages,
    )
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


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, object, object]:
    """
    Check ``bot_env``'s updates once a test passed, if it asks to.

    In the call phase rather than at teardown, so the check fails
    the test itself; a test that already failed is not checked.
    """
    result = yield
    funcargs = getattr(item, "funcargs", {})
    environment = funcargs.get("bot_env")
    if funcargs.get("bot_env_assert_updates_handled") and isinstance(
        environment,
        BotTestEnvironment,
    ):
        __tracebackhide__ = True
        environment.assert_updates_handled()
    return result


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
    """
    Same type, same payload, different bot — the only thing left to disagree about.

    The dump is guarded because this hook runs on **every** failing ``==`` in every project
    that installs aiogram, whether or not it uses the toolkit: pydantic-core's serializer
    gives up on a deep graph and reports the depth as a circular reference, and an
    explanation that raises replaces the user's real assertion failure with its own
    traceback. A comparison this cannot explain is one it declines to explain.
    """
    if not isinstance(left, TelegramObject) or not isinstance(right, TelegramObject):
        return False
    if type(left) is not type(right) or left.bot is right.bot:
        return False
    try:
        return left.model_dump() == right.model_dump()
    except Exception:
        return False


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
