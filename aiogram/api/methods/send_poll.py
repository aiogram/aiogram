from typing import Any, Dict, List, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod


class SendPoll(TelegramMethod[Message]):
    """
    Use this method to send a native poll. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendpoll
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    question: str
    """Poll question, 1-255 characters"""
    options: List[str]
    """A JSON-serialized list of answer options, 2-10 strings 1-100 characters each"""
    is_anonymous: Optional[bool] = None
    """True, if the poll needs to be anonymous, defaults to True"""
    type: Optional[str] = None
    """Poll type, 'quiz' or 'regular', defaults to 'regular'"""
    allows_multiple_answers: Optional[bool] = None
    """True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to
    False"""
    correct_option_id: Optional[int] = None
    """0-based identifier of the correct answer option, required for polls in quiz mode"""
    is_closed: Optional[bool] = None
    """Pass True, if the poll needs to be immediately closed. This can be useful for poll preview."""
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

        return Request(method="sendPoll", data=data)
