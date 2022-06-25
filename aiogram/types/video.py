from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class Video(TelegramObject):
    """
    This object represents a video file.

    Source: https://core.telegram.org/bots/api#video
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    width: int
    """Video width as defined by sender"""
    height: int
    """Video height as defined by sender"""
    duration: int
    """Duration of the video in seconds as defined by sender"""
    thumb: Optional[PhotoSize] = None
    """*Optional*. Video thumbnail"""
    file_name: Optional[str] = None
    """*Optional*. Original filename as defined by sender"""
    mime_type: Optional[str] = None
    """*Optional*. MIME type of the file as defined by sender"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes. It can be bigger than 2^31 and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this value."""
