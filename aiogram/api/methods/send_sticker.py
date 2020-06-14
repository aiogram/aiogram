from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class SendSticker(TelegramMethod[Message]):
    """
    Use this method to send static .WEBP or animated .TGS stickers. On success, the sent Message
    is returned.

    Source: https://core.telegram.org/bots/api#sendsticker
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    sticker: Union[InputFile, str]
    """Sticker to send. Pass a file_id as String to send a file that exists on the Telegram
    servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from
    the Internet, or upload a new one using multipart/form-data."""
    disable_notification: Optional[bool] = None
    """Sends the message silently. Users will receive a notification with no sound."""
    reply_to_message_id: Optional[int] = None
    """If the message is a reply, ID of the original message"""
    reply_markup: Optional[
        Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
    ] = None
    """Additional interface options. A JSON-serialized object for an inline keyboard, custom reply
    keyboard, instructions to remove reply keyboard or to force a reply from the user."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"sticker"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="sticker", value=self.sticker)

        return Request(method="sendSticker", data=data, files=files)
