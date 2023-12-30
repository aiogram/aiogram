from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from .base import UNSET_PARSE_MODE, TelegramObject

if TYPE_CHECKING:
    from .message_entity import MessageEntity


class ReplyParameters(TelegramObject):
    """
    Describes reply parameters for the message that is being sent.

    Source: https://core.telegram.org/bots/api#replyparameters
    """

    message_id: int
    """Identifier of the message that will be replied to in the current chat, or in the chat *chat_id* if it is specified"""
    chat_id: Optional[Union[int, str]] = None
    """*Optional*. If the message to be replied to is from a different chat, unique identifier for the chat or username of the channel (in the format :code:`@channelusername`)"""
    allow_sending_without_reply: Optional[bool] = None
    """*Optional*. Pass :code:`True` if the message should be sent even if the specified message to be replied to is not found; can be used only for replies in the same chat and forum topic."""
    quote: Optional[str] = None
    """*Optional*. Quoted part of the message to be replied to; 0-1024 characters after entities parsing. The quote must be an exact substring of the message to be replied to, including *bold*, *italic*, *underline*, *strikethrough*, *spoiler*, and *custom_emoji* entities. The message will fail to send if the quote isn't found in the original message."""
    quote_parse_mode: Optional[str] = UNSET_PARSE_MODE
    """*Optional*. Mode for parsing entities in the quote. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    quote_entities: Optional[List[MessageEntity]] = None
    """*Optional*. A JSON-serialized list of special entities that appear in the quote. It can be specified instead of *quote_parse_mode*."""
    quote_position: Optional[int] = None
    """*Optional*. Position of the quote in the original message in UTF-16 code units"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            message_id: int,
            chat_id: Optional[Union[int, str]] = None,
            allow_sending_without_reply: Optional[bool] = None,
            quote: Optional[str] = None,
            quote_parse_mode: Optional[str] = UNSET_PARSE_MODE,
            quote_entities: Optional[List[MessageEntity]] = None,
            quote_position: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                message_id=message_id,
                chat_id=chat_id,
                allow_sending_without_reply=allow_sending_without_reply,
                quote=quote,
                quote_parse_mode=quote_parse_mode,
                quote_entities=quote_entities,
                quote_position=quote_position,
                **__pydantic_kwargs,
            )
