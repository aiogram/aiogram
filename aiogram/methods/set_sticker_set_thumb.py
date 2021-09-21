from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from ..types import InputFile
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetStickerSetThumb(TelegramMethod[bool]):
    """
    Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickersetthumb
    """

    __returning__ = bool

    name: str
    """Sticker set name"""
    user_id: int
    """User identifier of the sticker set owner"""
    thumb: Optional[Union[InputFile, str]] = None
    """A **PNG** image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a **TGS** animation with the thumbnail up to 32 kilobytes in size; see `https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_`https://core.telegram.org/animated_stickers#technical-requirements <https://core.telegram.org/animated_stickers#technical-requirements>`_ for animated sticker technical requirements. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. :ref:`More info on Sending Files » <sending-files>`. Animated sticker set thumbnail can't be uploaded via HTTP URL."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"thumb"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="thumb", value=self.thumb)

        return Request(method="setStickerSetThumb", data=data, files=files)
