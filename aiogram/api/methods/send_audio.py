from typing import Any, Dict, Optional, Union

from ..types import (
    UNSET,
    ForceReply,
    InlineKeyboardMarkup,
    InputFile,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from .base import Request, TelegramMethod, prepare_file


class SendAudio(TelegramMethod[Message]):
    """
    Use this method to send audio files, if you want Telegram clients to display them in the music
    player. Your audio must be in the .MP3 or .M4A format. On success, the sent Message is
    returned. Bots can currently send audio files of up to 50 MB in size, this limit may be
    changed in the future.
    For sending voice messages, use the sendVoice method instead.

    Source: https://core.telegram.org/bots/api#sendaudio
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    audio: Union[InputFile, str]
    """Audio file to send. Pass a file_id as String to send an audio file that exists on the
    Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio
    file from the Internet, or upload a new one using multipart/form-data."""
    caption: Optional[str] = None
    """Audio caption, 0-1024 characters after entities parsing"""
    parse_mode: Optional[str] = UNSET
    """Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or
    inline URLs in the media caption."""
    duration: Optional[int] = None
    """Duration of the audio in seconds"""
    performer: Optional[str] = None
    """Performer"""
    title: Optional[str] = None
    """Track name"""
    thumb: Optional[Union[InputFile, str]] = None
    """Thumbnail of the file sent; can be ignored if thumbnail generation for the file is
    supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size.
    A thumbnail‘s width and height should not exceed 320. Ignored if the file is not uploaded
    using multipart/form-data. Thumbnails can’t be reused and can be only uploaded as a new
    file, so you can pass 'attach://<file_attach_name>' if the thumbnail was uploaded using
    multipart/form-data under <file_attach_name>."""
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
        data: Dict[str, Any] = self.dict(exclude={"audio", "thumb"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="audio", value=self.audio)
        prepare_file(data=data, files=files, name="thumb", value=self.thumb)

        return Request(method="sendAudio", data=data, files=files)
