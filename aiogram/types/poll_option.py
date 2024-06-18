from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class PollOption(TelegramObject):
    """
    This object contains information about one answer option in a poll.

    Source: https://core.telegram.org/bots/api#polloption
    """

    text: str
    """Option text, 1-100 characters"""
    voter_count: int
    """Number of users that voted for this option"""
    text_entities: Optional[List[MessageEntity]] = None
    """*Optional*. Special entities that appear in the option *text*. Currently, only custom emoji entities are allowed in poll option texts"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: str,
            voter_count: int,
            text_entities: Optional[List[MessageEntity]] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                voter_count=voter_count,
                text_entities=text_entities,
                **__pydantic_kwargs,
            )
