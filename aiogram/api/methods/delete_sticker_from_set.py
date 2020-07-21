from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .base import Request, TelegramMethod

if TYPE_CHECKING:  # pragma: no cover
    from ..client.bot import Bot


class DeleteStickerFromSet(TelegramMethod[bool]):
    """
    Use this method to delete a sticker from a set created by the bot. Returns True on success.

    Source: https://core.telegram.org/bots/api#deletestickerfromset
    """

    __returning__ = bool

    sticker: str
    """File identifier of the sticker"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="deleteStickerFromSet", data=data)
