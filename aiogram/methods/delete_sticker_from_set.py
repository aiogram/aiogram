from __future__ import annotations

from typing import TYPE_CHECKING

from .base import TelegramMethod


class DeleteStickerFromSet(TelegramMethod[bool]):
    """
    Use this method to delete a sticker from a set created by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#deletestickerfromset
    """

    __returning__ = bool
    __api_method__ = "deleteStickerFromSet"

    sticker: str
    """File identifier of the sticker"""
