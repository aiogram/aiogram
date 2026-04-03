from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject
from .custom import DateTime

if TYPE_CHECKING:
    from .chat import Chat
    from .message_entity import MessageEntity
    from .user import User


class PollOption(TelegramObject):
    """
    This object contains information about one answer option in a poll.

    Source: https://core.telegram.org/bots/api#polloption
    """

    persistent_id: str
    """Unique identifier of the option, persistent across option additions and deletions"""
    text: str
    """Option text, 1-100 characters"""
    voter_count: int
    """Number of users that voted for this option"""
    text_entities: list[MessageEntity] | None = None
    """*Optional*. Special entities that appear in the option *text*. Currently, only custom emoji entities are allowed in poll option texts"""
    added_by_user: User | None = None
    """*Optional*. The user who added the option, if it was added after poll creation"""
    added_by_chat: Chat | None = None
    """*Optional*. The chat that added the option, if it was added after poll creation"""
    addition_date: DateTime | None = None
    """*Optional*. Point in time (Unix timestamp) when the option was added"""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            persistent_id: str,
            text: str,
            voter_count: int,
            text_entities: list[MessageEntity] | None = None,
            added_by_user: User | None = None,
            added_by_chat: Chat | None = None,
            addition_date: DateTime | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                persistent_id=persistent_id,
                text=text,
                voter_count=voter_count,
                text_entities=text_entities,
                added_by_user=added_by_user,
                added_by_chat=added_by_chat,
                addition_date=addition_date,
                **__pydantic_kwargs,
            )
