from typing import Any, Dict

from .base import Request, TelegramMethod


class SetStickerPositionInSet(TelegramMethod[bool]):
    """
    Use this method to move a sticker in a set created by the bot to a specific position . Returns
    True on success.

    Source: https://core.telegram.org/bots/api#setstickerpositioninset
    """

    __returning__ = bool

    sticker: str
    """File identifier of the sticker"""
    position: int
    """New sticker position in the set, zero-based"""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="setStickerPositionInSet", data=data)
