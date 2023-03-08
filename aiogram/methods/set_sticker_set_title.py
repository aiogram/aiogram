from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetStickerSetTitle(TelegramMethod[bool]):
    """
    Use this method to set the title of a created sticker set. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickersettitle
    """

    __returning__ = bool

    name: str
    """Sticker set name"""
    title: str
    """Sticker set title, 1-64 characters"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setStickerSetTitle", data=data)
