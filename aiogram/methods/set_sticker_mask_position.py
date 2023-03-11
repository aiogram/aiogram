from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..types import MaskPosition
from .base import TelegramMethod


class SetStickerMaskPosition(TelegramMethod[bool]):
    """
    Use this method to change the `mask position <https://core.telegram.org/bots/api#maskposition>`_ of a mask sticker. The sticker must belong to a sticker set that was created by the bot. Returns :code:`True` on success.

    Source: https://core.telegram.org/bots/api#setstickermaskposition
    """

    __returning__ = bool
    __api_method__ = "setStickerMaskPosition"

    sticker: str
    """File identifier of the sticker"""
    mask_position: Optional[MaskPosition] = None
    """A JSON-serialized object with the position where the mask should be placed on faces. Omit the parameter to remove the mask position."""
