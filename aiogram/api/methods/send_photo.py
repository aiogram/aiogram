from typing import Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_file


class SendPhoto(TelegramMethod[Message]):
    """
    Use this method to send photos. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendphoto
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    photo: Union[InputFile, str]
    """Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers
    (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet,
    or upload a new photo using multipart/form-data."""
    caption: Optional[str] = None
    """Photo caption (may also be used when resending photos by file_id), 0-1024 characters after
    entities parsing"""
    parse_mode: Optional[str] = None
    """Mode for parsing entities in the photo caption. See formatting options for more details."""
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
        data: Dict[str, Any] = self.dict(exclude={"photo"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="photo", value=self.photo)

        return Request(method="sendPhoto", data=data, files=files)
