from __future__ import annotations

from .base import TelegramMethod


class SetStickerPositionInSet(TelegramMethod[bool]):
    """
    Use this method to move a sticker in a set created by the bot to a specific position. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickerpositioninset
    """

    __returning__ = bool
    __api_method__ = "setStickerPositionInSet"

    sticker: str
    """File identifier of the sticker"""
    position: int
    """New sticker position in the set, zero-based"""
