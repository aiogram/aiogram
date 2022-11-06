from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import InlineKeyboardMarkup, InputFile, InputMedia, Message
from .base import Request, TelegramMethod, prepare_media_file, prepare_parse_mode

if TYPE_CHECKING:
    from ..client.bot import Bot


class EditMessageMedia(TelegramMethod[Union[Message, bool]]):
    """
    Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited :class:`aiogram.types.message.Message` is returned, otherwise :code:`True` is returned.

    Source: https://core.telegram.org/bots/api#editmessagemedia
    """

    __returning__ = Union[Message, bool]

    media: InputMedia
    """A JSON-serialized object for a new media content of the message"""
    chat_id: Optional[Union[int, str]] = None
    """Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format :code:`@channelusername`)"""
    message_id: Optional[int] = None
    """Required if *inline_message_id* is not specified. Identifier of the message to edit"""
    inline_message_id: Optional[str] = None
    """Required if *chat_id* and *message_id* are not specified. Identifier of the inline message"""
    reply_markup: Optional[InlineKeyboardMarkup] = None
    """A JSON-serialized object for a new `inline keyboard <https://core.telegram.org/bots/features#inline-keyboards>`_."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()
        prepare_parse_mode(bot, data["media"])
        files: Dict[str, InputFile] = {}
        prepare_media_file(data=data, files=files)

        return Request(method="editMessageMedia", data=data, files=files)
