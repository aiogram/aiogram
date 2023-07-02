from __future__ import annotations

from ..types import StickerSet
from .base import TelegramMethod


class GetStickerSet(TelegramMethod[StickerSet]):
    """
    Use this method to get a sticker set. On success, a :class:`aiogram.types.sticker_set.StickerSet` object is returned.

    Source: https://core.telegram.org/bots/api#getstickerset
    """

    __returning__ = StickerSet
    __api_method__ = "getStickerSet"

    name: str
    """Name of the sticker set"""
