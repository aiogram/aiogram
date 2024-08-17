from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Optional, Union

from pydantic import Field

from ..client.default import Default
from ..types import (
    UNSET_PARSE_MODE,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    MessageEntity,
)
from .base import TelegramMethod


class EditMessageText(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit text and `game <https://core.telegram.org/bots/api#games>`_ messages. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned. Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within **48 hours** from the time they were sent.

    Source: https://core.telegram.org/bots/api#editmessagetext
    """

    __returning__ = Union[Message, bool]
    __api_method__ = "editMessageText"

    text: str
    """New text of the message, 1-4096 characters after entities parsing"""
    business_connection_id: Optional[str] = None
    """Unique identifier of the business connection on behalf of which the message to be edited was sent"""
    chat_id: Optional[Union[int, str]] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""
    parse_mode: Optional[Union[str, Default]] = Default("parse_mode")
    """Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    entities: Optional[List[MessageEntity]] = None
    """A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*"""
    link_preview_options: Optional[Union[LinkPreviewOptions, Default]] = Default("link_preview")
    """Link preview generation options for the message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_."""
    disable_web_page_preview: Optional[Union[bool, Default]] = Field(
        Default("link_preview_is_disabled"), json_schema_extra={"deprecated": True}
    )
    """Disables link previews for links in this message

.. deprecated:: API:7.0
   https://core.telegram.org/bots/api-changelog#december-29-2023"""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            text: str,
            business_connection_id: Optional[str] = None,
            chat_id: Optional[Union[int, str]] = None,
            message_id: Optional[int] = None,
            inline_message_id: Optional[str] = None,
            parse_mode: Optional[Union[str, Default]] = Default("parse_mode"),
            entities: Optional[List[MessageEntity]] = None,
            link_preview_options: Optional[Union[LinkPreviewOptions, Default]] = Default(
                "link_preview"
            ),
            reply_markup: Optional[InlineKeyboardMarkup] = None,
            disable_web_page_preview: Optional[Union[bool, Default]] = Default(
                "link_preview_is_disabled"
            ),
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                text=text,
                business_connection_id=business_connection_id,
                chat_id=chat_id,
                message_id=message_id,
                inline_message_id=inline_message_id,
                parse_mode=parse_mode,
                entities=entities,
                link_preview_options=link_preview_options,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_web_page_preview,
                **__pydantic_kwargs,
            )
