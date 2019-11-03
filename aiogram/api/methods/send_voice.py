from typing import Any, Dict, Optional, Union

from ..types import (
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod


class SendVoice(TelegramMethod[Message]):
    """
    Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .ogg file encoded with OPUS (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

    Source: https://core.telegram.org/bots/api#sendvoice
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format @channelusername)"""

    voice: Union[InputFile, str]
    """Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data."""

    caption: Optional[str] = None
    """Voice message caption, 0-1024 characters"""

    parse_mode: Optional[str] = None
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in the media caption."""

    duration: Optional[int] = None
    """Duration of the voice message in seconds"""

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
        files: Dict[str, Any] = {}
        return Request(method="sendVoice", data=data, files=files)
