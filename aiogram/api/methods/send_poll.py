from typing import Any, Dict, List, Optional, Union

from .base import Request, TelegramMethod
from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


class SendPoll(TelegramMethod[Message]):
    """
    Use this method to send a native poll. A native poll can't be sent to a private chat. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendpoll
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername). A native poll can't be sent to a private chat."""

    question: str
    """Poll question, 1-255 characters"""

    options: List[str]
    """List of answer options, 2-10 strings 1-100 characters each"""

    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""

    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""

    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="sendPoll", data=data)
