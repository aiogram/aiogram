from __future__ import annotations

from typing import TYPE_CHECKING, List

from .base import TelegramObject

if TYPE_CHECKING:
    from .photo_size import PhotoSize


class UserProfilePhotos(TelegramObject):
    """
    This object represent a user's profile pictures.

    Source: https://core.telegram.org/bots/api#userprofilephotos
    """

    total_count: int
    """Total number of profile pictures the target user has"""
    photos: List[List[PhotoSize]]
    """Requested profile pictures (in up to 4 sizes each)"""
