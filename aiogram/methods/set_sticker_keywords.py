from __future__ import annotations

from typing import List, Optional

from .base import TelegramMethod


class SetStickerKeywords(TelegramMethod[bool]):
    """
    Use this method to change search keywords assigned to a regular or custom emoji sticker. The sticker must belong to a sticker set created by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickerkeywords
    """

    __returning__ = bool
    __api_method__ = "setStickerKeywords"

    sticker: str
    """File identifier of the sticker"""
    keywords: Optional[List[str]] = None
    """A JSON-serialized list of 0-20 search keywords for the sticker with total length of up to 64 characters"""
