from __future__ import annotations

from .base import TelegramMethod


class SetStickerSetTitle(TelegramMethod[bool]):
    """
    Use this method to set the title of a created sticker set. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickersettitle
    """

    __returning__ = bool
    __api_method__ = "setStickerSetTitle"

    name: str
    """Sticker set name"""
    title: str
    """Sticker set title, 1-64 characters"""
