from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from ..client.default import Default
from ..types import UNSET_PARSE_MODE, InlineKeyboardMarkup, Message, MessageEntity
from .base import TelegramMethod


class EditMessageCaption(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editmessagecaption
    """

    __returning__ = Union[Message, bool]
    __api_method__ = "editMessageCaption"

    chat_id: Optional[Union[int, str]] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""
    caption: Optional[str] = None
    """New caption of the message, 0-1024 characters after entities parsing"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """Mode for parsing entities in the message caption. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    caption_entities: Optional[List[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            chat_id: Optional[Union[int, str]] = None,
            message_id: Optional[int] = None,
            inline_message_id: Optional[str] = None,
            caption: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            caption_entities: Optional[List[MessageEntity]] = None,
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                chat_id=chat_id,
                message_id=message_id,
                inline_message_id=inline_message_id,
                caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                reply_markup=reply_markup,
                **__pydantic_kwargs,
            )
