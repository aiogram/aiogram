from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import UNSET, InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class EditMessageText(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit text and game messages. On success, if edited message is sent by the
    bot, the edited Message is returned, otherwise True is returned.

    Source: https://core.telegram.org/bots/api#editmessagetext
    """

    __returning__ = Union[Message, bool]

    text: str
    """New text of the message, 1-4096 characters after entities parsing"""
    chat_id: Optional[Union[int, str]] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat or
    username of the target channel (in the format @channelusername)"""
    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""
    parse_mode: Optional[str] = UNSET
    """Mode for parsing entities in the message text. See formatting options for more details."""
    disable_web_page_preview: Optional[bool] = None
    """Disables link previews for links in this message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an inline keyboard."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="editMessageText", data=data)
