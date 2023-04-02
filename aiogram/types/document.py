from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class Document(TelegramObject):
    """
    This object represents a general file (as opposed to `photos <https://core.telegram.org/bots/api#photosize>`_, `voice messages <https://core.telegram.org/bots/api#voice>`_ and `audio files <https://core.telegram.org/bots/api#audio>`_).

    Source: https://core.telegram.org/bots/api#document
    """

    file_id: str
    """Identifier for this file, which can be used to download or reuse the file"""
    file_unique_id: str
    """Unique identifier for this file, which is supposed to be the same over time and for different bots. Can't be used to download or reuse the file."""
    thumbnail: Optional[PhotoSize] = None
    """*Optional*. Document thumbnail as defined by sender"""
    file_name: Optional[str] = None
    """*Optional*. Original filename as defined by sender"""
    mime_type: Optional[str] = None
    """*Optional*. MIME type of the file as defined by sender"""
    file_size: Optional[int] = None
    """*Optional*. File size in bytes. It can be bigger than 2^31 and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this value."""
