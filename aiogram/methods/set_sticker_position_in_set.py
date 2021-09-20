from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class SetStickerPositionInSet(TelegramMethod[bool]):
    """
    Use this method to move a sticker in a set created by the bot to a specific position. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickerpositioninset
    """

    __returning__ = bool

    sticker: str
    """File identifier of the sticker"""
    position: int
    """New sticker position in the set, zero-based"""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setStickerPositionInSet", data=data)
