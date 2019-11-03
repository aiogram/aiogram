from __future__ import annotations

from typing import Optional

from .base import TelegramObject


class Voice(TelegramObject):
    """
    This object represents a voice note.

    Source: https://core.telegram.org/bots/api#voice
    """

    file_id: str
    """Identifier for this file"""
    duration: int
    """Duration of the audio in seconds as defined by sender"""
    mime_type: Optional[str] = None
    """MIME type of the file as defined by sender"""
    file_size: Optional[int] = None
    """File size"""
