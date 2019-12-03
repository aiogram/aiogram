import secrets
from typing import Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, InputFile, InputMedia, Message
from .base import Request, TelegramMethod


class EditMessageMedia(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit animation, audio, document, photo, or video messages. If a message is
    a part of a message album, then it can be edited only to a photo or a video. Otherwise,
    message type can be changed arbitrarily. When inline message is edited, new file can't be
    uploaded. Use previously uploaded file via its file_id or specify a URL. On success, if the
    edited message was sent by the bot, the edited Message is returned, otherwise True is
    returned.

    Source: https://core.telegram.org/bots/api#editmessagemedia
    """

    __returning__ = Union[Message, bool]

    media: InputMedia
    """A JSON-serialized object for a new media content of the message"""
    chat_id: Optional[Union[int, str]] = None
    """Required if inline_message_id is not specified. Unique identifier for the target chat or
    username of the target channel (in the format @channelusername)"""
    message_id: Optional[int] = None
    """Required if inline_message_id is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if chat_id and message_id are not specified. Identifier of the inline message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new inline keyboard."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()
        self.prepare_parse_mode(data["media"])

        files: Dict[str, InputFile] = {}
        self.prepare_media_file(data=data, files=files)

        return Request(method="editMessageMedia", data=data, files=files)

    def prepare_media_file(self, data: Dict[str, Any], files: Dict[str, InputFile]) -> None:
        if (
            data["media"]
            and "media" in data["media"]
            and isinstance(data["media"]["media"], InputFile)
        ):
            tag = secrets.token_urlsafe(10)
            files[tag] = data["media"].pop("media")  # type: ignore
            data["media"]["media"] = f"attach://{tag}"
