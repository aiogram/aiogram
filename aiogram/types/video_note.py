from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class VideoNote(TelegramObject):
    """
    This object represents a `video message <https://telegram.org/blog/video-messages-and-telescope>`_ (available in Telegram apps as of `v.4.0 <https://telegram.org/blog/video-messages-and-telescope>`_).

    Source: https://core.telegram.org/bots/api#videonote
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    length: int
    """Video width and height (diameter of the video message) as defined by sender"""
    duration: int
    """Duration of the video in seconds as defined by sender"""
    thumb: Optional[PhotoSize] = None
    """*Optional*. Video thumbnail"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes"""
