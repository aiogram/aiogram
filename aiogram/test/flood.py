"""
Telegram's flood limits, modeled per chat when a test asks for them.

Off by default: a test passes ``BotTestEnvironment(rate_limits=
RateLimits())`` to have the bot's sends refused the way Telegram
refuses a bot that floods a chat, with a 429 and a ``retry_after``
that is the truth about when the next send goes through.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from aiogram.enums import ChatType
from aiogram.methods import (
    CopyMessage,
    CopyMessages,
    ForwardMessage,
    ForwardMessages,
    SendMediaGroup,
    SendMessage,
    SendPoll,
    TelegramMethod,
)

from .modeling import MEDIA_FIELDS

#: The methods a rate limit counts: each call puts one message, or
#: one album or batch, into a chat.
RATE_LIMITED_METHODS: frozenset[type[TelegramMethod[Any]]] = frozenset(
    {
        SendMessage,
        SendPoll,
        SendMediaGroup,
        ForwardMessage,
        ForwardMessages,
        CopyMessage,
        CopyMessages,
        *MEDIA_FIELDS,
    },
)


@dataclass(frozen=True)
class RateLimit:
    """At most ``messages`` sends into one chat in any ``seconds``."""

    messages: int
    seconds: float


@dataclass(frozen=True)
class RateLimits:
    """
    How fast the bot may send into one chat.

    The defaults are Telegram's guidance in its bot FAQ: about one
    message per second in a chat, and at most 20 per minute in a
    group, shared by all its topics. Pass ``None`` to drop one of
    them, or a :class:`RateLimit` of your own. Telegram tolerates
    short bursts above the first; the model does not.
    """

    #: Applies in every chat.
    per_chat: RateLimit | None = RateLimit(messages=1, seconds=1.0)
    #: Applies in groups and supergroups as well.
    per_group: RateLimit | None = RateLimit(messages=20, seconds=60.0)

    def for_chat(self, chat_type: str) -> list[RateLimit]:
        """The limits a chat of ``chat_type`` is held to."""
        limits = [self.per_chat]
        if chat_type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            limits.append(self.per_group)
        return [limit for limit in limits if limit is not None]


@dataclass
class FloodControl:
    """
    When the bot sent into each chat, and whether it may again.

    Times are seconds on the clock the environment hands in, which
    is the event loop's: a looptime loop moves it, and so does
    :meth:`aiogram.test.BotTestEnvironment.advance_time`.
    """

    limits: RateLimits
    sent: dict[int, deque[float]] = field(default_factory=dict)

    def retry_after(self, chat_id: int, chat_type: str, now: float) -> int | None:
        """
        The whole seconds until a send into the chat is allowed.

        ``None`` when one is allowed now. Rounded up, so a bot that
        waits exactly that long gets through.
        """
        stamps = self.sent.get(chat_id, deque())
        wait = 0.0
        for limit in self.limits.for_chat(chat_type):
            recent = [stamp for stamp in stamps if now - stamp < limit.seconds]
            if len(recent) >= limit.messages:
                oldest = recent[len(recent) - limit.messages]
                wait = max(wait, oldest + limit.seconds - now)
        if wait <= 0:
            return None
        return max(1, math.ceil(wait))

    def record(self, chat_id: int, chat_type: str, now: float) -> None:
        """Count a send into the chat, forgetting old ones."""
        stamps = self.sent.setdefault(chat_id, deque())
        stamps.append(now)
        horizon = max(
            (limit.seconds for limit in self.limits.for_chat(chat_type)),
            default=0.0,
        )
        while stamps and now - stamps[0] >= horizon:
            stamps.popleft()
