from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from ..types import UserProfilePhotos
from .base import Request, TelegramMethod

if TYPE_CHECKING:
    from ..client.bot import Bot


class GetUserProfilePhotos(TelegramMethod[UserProfilePhotos]):
    """
    Use this method to get a list of profile pictures for a user. Returns a :class:`aiogram.types.user_profile_photos.UserProfilePhotos` object.

    Source: https://core.telegram.org/bots/api#getuserprofilephotos
    """

    __returning__ = UserProfilePhotos

    user_id: int
    """Unique identifier of the target user"""
    offset: Optional[int] = None
    """Sequential number of the first photo to be returned. By default, all photos are returned."""
    limit: Optional[int] = None
    """Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100."""

    def build_request(self, bot: Bot) -> Request:
        data: Dict[str, Any] = self.dict()

        return Request(method="getUserProfilePhotos", data=data)
