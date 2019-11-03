from typing import Any, Dict

from ..types import StickerSet
from .base import Request, TelegramMethod


class GetStickerSet(TelegramMethod[StickerSet]):
    """
    Use this method to get a sticker set. On success, a StickerSet object is returned.

    Source: https://core.telegram.org/bots/api#getstickerset
    """

    __returning__ = StickerSet

    name: str
    """Name of the sticker set"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})
        files: Dict[str, Any] = {}
        return Request(method="getStickerSet", data=data, files=files)
