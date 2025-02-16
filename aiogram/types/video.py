from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional

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
    """Video width as defined by the sender"""
    height: int
    """Video height as defined by the sender"""
    duration: int
    """Duration of the video in seconds as defined by the sender"""
    thumbnail: Optional[PhotoSize] = None
    """*Optional*. Video thumbnail"""
    cover: Optional[list[PhotoSize]] = None
    """*Optional*. Available sizes of the cover of the video in the message"""
    start_timestamp: Optional[datetime.datetime] = None
    """*Optional*. Timestamp in seconds from which the video will play in the message"""
    file_name: Optional[str] = None
    """*Optional*. Original filename as defined by the sender"""
    mime_type: Optional[str] = None
    """*Optional*. MIME type of the file as defined by the sender"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes. It can be bigger than 2^31 and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this value."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            file_id: str,
            file_unique_id: str,
            width: int,
            height: int,
            duration: int,
            thumbnail: Optional[PhotoSize] = None,
            cover: Optional[list[PhotoSize]] = None,
            start_timestamp: Optional[datetime.datetime] = None,
            file_name: Optional[str] = None,
            mime_type: Optional[str] = None,
            file_size: Optional[int] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                file_id=file_id,
                file_unique_id=file_unique_id,
                width=width,
                height=height,
                duration=duration,
                thumbnail=thumbnail,
                cover=cover,
                start_timestamp=start_timestamp,
                file_name=file_name,
                mime_type=mime_type,
                file_size=file_size,
                **__pydantic_kwargs,
            )
