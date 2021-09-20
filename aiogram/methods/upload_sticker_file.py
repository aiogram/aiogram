from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from ..types import File, InputFile
from .base import Request, TelegramMethod, prepare_file

if TYPE_CHECKING:
    from ..client.bot import Bot


class UploadStickerFile(TelegramMethod[File]):
    """
    Use this method to upload a .PNG file with a sticker for later use in *createNewStickerSet* and *addStickerToSet* methods (can be used multiple times). Returns the uploaded :class:`aiogram.types.file.File` on success.

    Source: https://core.telegram.org/bots/api#uploadstickerfile
    """

    __returning__ = File

    user_id: int
    """User identifier of sticker file owner"""
    png_sticker: InputFile
    """**PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. :ref:`More info on Sending Files » <sending-files>`"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict(exclude={"png_sticker"})

        files: Dict[str, InputFile] = {}
        prepare_file(data=data, files=files, name="png_sticker", value=self.png_sticker)

        return Request(method="uploadStickerFile", data=data, files=files)
