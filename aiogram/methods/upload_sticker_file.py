from __future__ import annotations

from ..types import File, InputFile
from .base import TelegramMethod


class UploadStickerFile(TelegramMethod[File]):
    """
    Use this method to upload a file with a sticker for later use in the :class:`aiogram.methods.create_new_sticker_set.CreateNewStickerSet` and :class:`aiogram.methods.add_sticker_to_set.AddStickerToSet` methods (the file can be used multiple times). Returns the uploaded :class:`aiogram.types.file.File` on success.

    Source: https://core.telegram.org/bots/api#uploadstickerfile
    """

    __returning__ = File
    __api_method__ = "uploadStickerFile"

    user_id: int
    """User identifier of sticker file owner"""
    sticker: InputFile
    """A file with the sticker in .WEBP, .PNG, .TGS, or .WEBM format. See `https://core.telegram.org/stickers <https://core.telegram.org/stickers>`_`https://core.telegram.org/stickers <https://core.telegram.org/stickers>`_ for technical requirements. :ref:`More information on Sending Files » <sending-files>`"""
    sticker_format: str
    """Format of the sticker, must be one of 'static', 'animated', 'video'"""
