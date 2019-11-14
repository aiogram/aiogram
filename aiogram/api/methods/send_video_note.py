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


class SendVideoNote(TelegramMethod[Message]):
    """
    As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use
    this method to send video messages. On success, the sent Message is returned.

    Source: https://core.telegram.org/bots/api#sendvideonote
    """

    __returning__ = Message

    chat_id: Union[int, str]
    """Unique identifier for the target chat or username of the target channel (in the format
    @channelusername)"""
    video_note: Union[InputFile, str]
    """Video note to send. Pass a file_id as String to send a video note that exists on the
    Telegram servers (recommended) or upload a new video using multipart/form-data.. Sending
    video notes by a URL is currently unsupported"""
    duration: Optional[int] = None
    """Duration of sent video in seconds"""
    length: Optional[int] = None
    """Video width and height, i.e. diameter of the video message"""
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
        data: Dict[str, Any] = self.dict(
            exclude={"video_note", "thumb",}
        )

        files: Dict[str, InputFile] = {}
        self.prepare_file(data=data, files=files, name="video_note", value=self.video_note)
        self.prepare_file(data=data, files=files, name="thumb", value=self.thumb)

        return Request(method="sendVideoNote", data=data, files=files)
