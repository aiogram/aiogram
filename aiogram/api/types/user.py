from __future__ import annotations

import typing
from typing import Optional

from ...utils import markdown
from .base import TelegramObject
from .parse_mode import ParseMode

if typing.TYPE_CHECKING:
    from ..methods import GetUserProfilePhotos  # pragma: no cover


class User(TelegramObject):
    """
    This object represents a Telegram user or bot.

    Source: https://core.telegram.org/bots/api#user
    """

    id: int
    """Unique identifier for this user or bot"""
    is_bot: bool
    """True, if this user is a bot"""
    first_name: str
    """User‘s or bot’s first name"""
    last_name: Optional[str] = None
    """User‘s or bot’s last name"""
    username: Optional[str] = None
    """User‘s or bot’s username"""
    language_code: Optional[str] = None
    """IETF language tag of the user's language"""
    can_join_groups: Optional[bool] = None
    """True, if the bot can be invited to groups. Returned only in getMe."""
    can_read_all_group_messages: Optional[bool] = None
    """True, if privacy mode is disabled for the bot. Returned only in getMe."""
    supports_inline_queries: Optional[bool] = None
    """True, if the bot supports inline queries. Returned only in getMe."""

    @property
    def full_name(self) -> str:
        """
        Get full name of user.
        """
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        """
        Get user's username to mention him.
        Full name will be returned if user has no username.
        """
        if self.username:
            return "@" + self.username
        return self.full_name

    @property
    def url(self) -> str:
        """
        Get user's profile url.
        """
        return f"tg://user?id={self.id}"

    def get_mention(self, name: Optional[str] = None, as_html: Optional[bool] = None) -> str:
        """
        Get user's mention url.

        :param name: Name of user in the mention link. User's full_name property will be used if not specified.
                     Defaults to None
        :param as_html: Boolean flag defining format of the resulting mention. Bot parse_mode property will be used if
                        not specified. Defaults to None
        """
        if (
            as_html is None
            and self.bot.parse_mode
            and self.bot.parse_mode.upper() == ParseMode.HTML
        ):
            as_html = True

        if name is None:
            name = self.full_name
        if as_html:
            return markdown.hlink(name, self.url)
        return markdown.link(name, self.url)

    def get_profile_photos(
        self, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> GetUserProfilePhotos:
        """
        Alias for bot method get_user_profile_photos.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned.
        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :return: GetUserProfilePhotos method object.
        """
        from aiogram.api.methods import GetUserProfilePhotos

        return GetUserProfilePhotos(user_id=self.id, offset=offset, limit=limit)
