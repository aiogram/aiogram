from typing import Any, Dict, Optional

from .base import Request, TelegramMethod
from ..types import UserProfilePhotos


class GetUserProfilePhotos(TelegramMethod[UserProfilePhotos]):
    """
    Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.

    Source: https://core.telegram.org/bots/api#getuserprofilephotos
    """

    __returning__ = UserProfilePhotos

    user_id: int
    """Unique identifier of the target user"""

    offset: Optional[int] = None
    """Sequential number of the first photo to be returned. By default, all photos are returned."""

    limit: Optional[int] = None
    """Limits the number of photos to be retrieved. Values between 1—100 are accepted. Defaults to 100."""

    def build_request(self) -> Request:
        data: Dict[str, Any] = self.dict(exclude_unset=True, exclude={})

        return Request(method="getUserProfilePhotos", data=data)
