from typing import Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod


class SendMessage(TelegramMethod[Message]):
    """
    Use this method to send text messages. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendmessage
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    text: str
    """Text of the message to be sent"""

    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in your bot's message."""

    disable_web_page_preview: Optional[bool] = None
    """Disables link previews for links in this message"""

    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""

    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""

    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="sendMessage", data=data)
