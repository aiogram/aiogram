from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import TelegramObject

if TYPE_CHECKING:
    from .maybe_inaccessible_message_union import MaybeInaccessibleMessageUnion
    from .message_entity import MessageEntity


class PollOptionDeleted(TelegramObject):
    """
    This object represents a service message about an option deleted from a poll.

    Source: https://core.telegram.org/bots/api#polloptiondeleted
    """

    option_persistent_id: str
    """Unique identifier of the deleted option"""
    option_text: str
    """Text of the deleted option, 1-100 characters"""
    poll_message: MaybeInaccessibleMessageUnion | None = None
    """*Optional*. The message containing the poll from which the option was deleted. Note that the :class:`aiogram.types.message.Message` object in this field will not contain the *reply_to_message* field even if it itself is a reply."""
    option_text_entities: list[MessageEntity] | None = None
    """*Optional*. Special entities that appear in the option text. Currently, only custom emoji entities are allowed in poll option texts"""

    if TYPE_CHECKING:

        def __init__(
            __pydantic__self__,
            *,
            option_persistent_id: str,
            option_text: str,
            poll_message: MaybeInaccessibleMessageUnion | None = None,
            option_text_entities: list[MessageEntity] | None = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            super().__init__(
                option_persistent_id=option_persistent_id,
                option_text=option_text,
                poll_message=poll_message,
                option_text_entities=option_text_entities,
                **__pydantic_kwargs,
            )
