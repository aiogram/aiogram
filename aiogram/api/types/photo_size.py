from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class PhotoSize(TelegramObject):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    Source: https://core.telegram.org/bots/api#photosize
    """

    file_id: str
    """Identifier for this file"""
    width: int
    """Photo width"""
    height: int
    """Photo height"""
    file_size: Optional[int] = None
    """File size"""
