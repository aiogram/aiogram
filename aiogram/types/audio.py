from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class Audio(TelegramObject):
    """
    This object represents an audio file to be treated as music by the Telegram clients.

    Source: https://core.telegram.org/bots/api#audio
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    duration: int
    """Duration of the audio in seconds as defined by sender"""
    performer: Optional[str] = None
    """*Optional*. Performer of the audio as defined by sender or by audio tags"""
    title: Optional[str] = None
    """*Optional*. Title of the audio as defined by sender or by audio tags"""
    file_name: Optional[str] = None
    """*Optional*. Original filename as defined by sender"""
    mime_type: Optional[str] = None
    """*Optional*. MIME type of the file as defined by sender"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes"""
    thumb: Optional[PhotoSize] = None
    """*Optional*. Thumbnail of the album cover to which the music file belongs"""
