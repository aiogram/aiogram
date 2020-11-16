from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class PhotoSize(TelegramObject):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    Source: https://core.telegram.org/bots/api#photosize
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for
    different bots. Can't be used to download or reuse the file."""
    width: int
    """Photo width"""
    height: int
    """Photo height"""
    file_size: Optional[int] = None
    """File size"""
