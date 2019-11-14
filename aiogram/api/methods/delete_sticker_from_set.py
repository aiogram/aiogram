from typing import Any, Dict

from .base import Request, TelegramMethod


class DeleteStickerFromSet(TelegramMethod[bool]):
    """
    Use this method to delete a sticker from a set created by the bot. Returns True on success.

    Source: https://core.telegram.org/bots/api#deletestickerfromset
    """

    __returning__ = bool

    sticker: str
    """File identifier of the sticker"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="deleteStickerFromSet", data=data)
