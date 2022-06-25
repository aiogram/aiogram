from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class Voice(TelegramObject):
    """
    This object represents a voice note.

    Source: https://core.telegram.org/bots/api#voice
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    duration: int
    """Duration of the audio in seconds as defined by sender"""
    mime_type: Optional[str] = None
    """*Optional*. MIME type of the file as defined by sender"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes. It can be bigger than 2^31 and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this value."""
