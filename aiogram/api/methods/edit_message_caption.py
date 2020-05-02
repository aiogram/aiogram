from typing import Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod, prepare_parse_mode


class EditMessageCaption(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit captions of messages. On success, if edited message is sent by the
    bot, the edited Message is returned, otherwise True is returned.

    Source: https://core.telegram.org/bots/api#editmessagecaption
    """

    __returning__ = Union[Message, bool]

    chat_id: Optional[Union[int, str]] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat or
    username of the target channel (in the format @channelusername)"""
    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""
    caption: Optional[str] = None
    """New caption of the message, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the message caption. See formatting options for more details."""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for an inline keyboard."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()
        prepare_parse_mode(data)

        return Request(method="editMessageCaption", data=data)
