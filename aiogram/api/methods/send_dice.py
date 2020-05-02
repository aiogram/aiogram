from typing import Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod


class SendDice(TelegramMethod[Message]):
    """
    Use this method to send a dice, which will have a random value from 1 to 6. On success, the
    sent Message is returned. (Yes, we're aware of the 'proper' singular of die. But it's awkward,
    and we decided to help it change. One dice at a time!)

    Source: https://core.telegram.org/bots/api#senddice
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    emoji: Optional[str] = None
    """Emoji on which the dice throw animation is based. Currently, must be one of '' or ''.
    Defauts to ''"""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply
    keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendDice", data=data)
