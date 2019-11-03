from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class VideoNote(TelegramObject):
    """
    This object represents a video message (available in Telegram apps as of v.4.0).

    Source: https://core.telegram.org/bots/api#videonote
    """

    file_id: str
    """Identifier for this file"""
    length: int
    """Video width and height (diameter of the video message) as defined by sender"""
    duration: int
    """Duration of the video in seconds as defined by sender"""
    thumb: Optional[PhotoSize] = None
    """Video thumbnail"""
    file_size: Optional[int] = None
    """File size"""
