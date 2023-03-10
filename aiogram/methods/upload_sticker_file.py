from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import File, InputFile
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class UploadStickerFile(TelegramMethod[File]):
    """
    Use this method to upload a file with a sticker for later use in the :class:`aiogram.methods.create_new_sticker_set.CreateNewStickerSet` and :class:`aiogram.methods.add_sticker_to_set.AddStickerToSet` methods (the file can be used multiple times). Returns the uploaded :class:`aiogram.types.file.File` on success.

    Source: https://core.telegram.org/bots/api#uploadstickerfile
    """

    __returning__ = File

    user_id: int
    """User identifier of sticker file owner"""
    sticker: InputFile
    """A file with the sticker in .WEBP, .PNG, .TGS, or .WEBM format. See `https://core.telegram.org/stickers <https://core.telegram.org/stickers>`_`https://core.telegram.org/stickers <https://core.telegram.org/stickers>`_ for technical requirements. :ref:`More information on Sending Files » <sending-files>`"""
    sticker_format: str
    """Format of the sticker, must be one of 'static', 'animated', 'video'"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"sticker"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="sticker", value=self.sticker)

        return Request(method="uploadStickerFile", data=data, files=files)
