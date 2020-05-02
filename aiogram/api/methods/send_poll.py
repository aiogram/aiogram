import datetime
from typing import Any, Dict, List, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_parse_mode


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
    explanation: Optional[str] = None
    """Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a
    quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing"""
    explanation_parse_mode: Optional[str] = None
    """Mode for parsing entities in the explanation. See formatting options for more details."""
    open_period: Optional[int] = None
    """Amount of time in seconds the poll will be active after creation, 5-600. Can't be used
    together with close_date."""
    close_date: Optional[Union[datetime.datetime, datetime.timedelta, int]] = None
    """Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least
    5 and no more than 600 seconds in the future. Can't be used together with open_period."""
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
        prepare_parse_mode(data, parse_mode_property="explanation_parse_mode")

        return Request(method="sendPoll", data=data)
