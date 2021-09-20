from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ..types import (
    UNSET,
    ForceReply,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendMessage(TelegramMethod[Message]):
    """
    Use this method to send text messages. On success, the sent :class:`aiogram.types.message.Message` is returned.

    Source: https://core.telegram.org/bots/api#sendmessage
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    text: str
    """Text of the message to be sent, 1-4096 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Mode for parsing entities in the message text. See `formatting options <https://core.telegram.org/bots/api#formatting-options>`_ for more details."""
    entities: Optional[List[MessageEntity]] = None
    """List of special entities that appear in message text, which can be specified instead of *parse_mode*"""
    disable_web_page_preview: Optional[bool] = None
    """Disables link previews for links in this message"""
    disable_notification: Optional[bool] = None
    """Sends the message `silently <https://telegram.org/blog/channels-2-0#silent-messages>`_. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    allow_sending_without_reply: Optional[bool] = None
    """Pass :code:`True`, if the message should be sent even if the specified replied-to message is not found"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an `inline keyboard <https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating>`_, `custom reply keyboard <https://core.telegram.org/bots#keyboards>`_, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        prepare_parse_mode(
            bot, data, parse_mode_property="parse_mode", entities_property="entities"
        )

        return Request(method="sendMessage", data=data)
