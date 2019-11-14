from typing import Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, Message
from .base import Request, TelegramMethod


class StopMessageLiveLocation(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to stop updating a live location message before live_period expires. On
    success, if the message was sent by the bot, the sent Message is returned, otherwise True is
    returned.

    Source: https://core.telegram.org/bots/api#stopmessagelivelocation
    """

    __returning__ = Union[Message, bool]

    chat_id: Optional[Union[int, str]] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat or
    username of the target channel (in the format @channelusername)"""
    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the message with live
    location to stop"""
    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new inline keyboard."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="stopMessageLiveLocation", data=data)
