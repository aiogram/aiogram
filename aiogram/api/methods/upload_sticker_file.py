from typing import Any, Dict

from ..types import File, InputFile
from .base import Request, TelegramMethod


class UploadStickerFile(TelegramMethod[File]):
    """
    Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet methods (can be used multiple times). Returns the uploaded File on success.

    Source: https://core.telegram.org/bots/api#uploadstickerfile
    """

    __returning__ = File

    user_id: int
    """User identifier of sticker file owner"""

    png_sticker: InputFile
    """Png image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})
        files: Dict[str, Any] = {}
        return Request(method="uploadStickerFile", data=data, files=files)
