from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..types.message_entity import MessageEntity
from .base import TelegramMethod


class SendGift(TelegramMethod[bool]):
    """
    Sends a gift to the given user. The gift can't be converted to Telegram Stars by the user. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#sendgift
    """

    __returning__ = bool
    __api_method__ = "sendGift"

    user_id: int
    """Unique identifier of the target user that will receive the gift"""
    gift_id: str
    """Identifier of the gift"""
    text: Optional[str] = None
    """Text that will be shown along with the gift; 0-255 characters"""
    text_parse_mode: Optional[str] = None
    """Mode for parsing entities in the text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details. Entities other than 'bold', 'italic', 'underline', 'strikethrough', 'spoiler', and 'custom_emoji' are ignored."""
    text_entities: Optional[list[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the gift text. It can be specified instead of *text_parse_mode*. Entities other than 'bold', 'italic', 'underline', 'strikethrough', 'spoiler', and 'custom_emoji' are ignored."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            user_id: int,
            gift_id: str,
            text: Optional[str] = None,
            text_parse_mode: Optional[str] = None,
            text_entities: Optional[list[MessageEntity]] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                user_id=user_id,
                gift_id=gift_id,
                text=text,
                text_parse_mode=text_parse_mode,
                text_entities=text_entities,
                **__pydantic_kwargs,
            )
