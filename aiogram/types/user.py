from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..utils import markdown
from ..utils.link import create_tg_link
from .base import TelegramObject

if TYPE_CHECKING:
    from ..methods import GetUserProfilePhotos


class User(TelegramObject):
    """
    This object represents a Telegram user or bot.

    Source: https://core.telegram.org/bots/api#user
    """

    id: int
    """Unique identifier for this user or bot. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier."""
    is_bot: bool
    """:code:`True`, if this user is a bot"""
    first_name: str
    """User's or bot's first name"""
    last_name: Optional[str] = None
    """*Optional*. User's or bot's last name"""
    username: Optional[str] = None
    """*Optional*. User's or bot's username"""
    language_code: Optional[str] = None
    """*Optional*. `IETF language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_ of the user's language"""
    is_premium: Optional[bool] = None
    """*Optional*. :code:`True`, if this user is a Telegram Premium user"""
    added_to_attachment_menu: Optional[bool] = None
    """*Optional*. :code:`True`, if this user added the bot to the attachment menu"""
    can_join_groups: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot can be invited to groups. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    can_read_all_group_messages: Optional[bool] = None
    """*Optional*. :code:`True`, if `privacy mode <https://core.telegram.org/bots/features#privacy-mode>`_ is disabled for the bot. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    supports_inline_queries: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot supports inline queries. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    can_connect_to_business: Optional[bool] = None
    """*Optional*. :code:`True`, if the bot can be connected to a Telegram Business account to receive its messages. Returned only in :class:`aiogram.methods.get_me.GetMe`."""

    if TYPE_CHECKING:
        # DO NOT EDIT MANUALLY!!!
        # This section was auto-generated via `butcher`

        def __init__(
            __pydantic__self__,
            *,
            id: int,
            is_bot: bool,
            first_name: str,
            last_name: Optional[str] = None,
            username: Optional[str] = None,
            language_code: Optional[str] = None,
            is_premium: Optional[bool] = None,
            added_to_attachment_menu: Optional[bool] = None,
            can_join_groups: Optional[bool] = None,
            can_read_all_group_messages: Optional[bool] = None,
            supports_inline_queries: Optional[bool] = None,
            can_connect_to_business: Optional[bool] = None,
            **__pydantic_kwargs: Any,
        ) -> None:
            # DO NOT EDIT MANUALLY!!!
            # This method was auto-generated via `butcher`
            # Is needed only for type checking and IDE support without any additional plugins

            super().__init__(
                id=id,
                is_bot=is_bot,
                first_name=first_name,
                last_name=last_name,
                username=username,
                language_code=language_code,
                is_premium=is_premium,
                added_to_attachment_menu=added_to_attachment_menu,
                can_join_groups=can_join_groups,
                can_read_all_group_messages=can_read_all_group_messages,
                supports_inline_queries=supports_inline_queries,
                can_connect_to_business=can_connect_to_business,
                **__pydantic_kwargs,
            )

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def url(self) -> str:
        return create_tg_link("user", id=self.id)

    def mention_markdown(self, name: Optional[str] = None) -> str:
        if name is None:
            name = self.full_name
        return markdown.link(name, self.url)

    def mention_html(self, name: Optional[str] = None) -> str:
        if name is None:
            name = self.full_name
        return markdown.hlink(name, self.url)

    def get_profile_photos(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> GetUserProfilePhotos:
        """
        Shortcut for method :class:`aiogram.methods.get_user_profile_photos.GetUserProfilePhotos`
        will automatically fill method attributes:

        - :code:`user_id`

        Use this method to get a list of profile pictures for a user. Returns a :class:`aiogram.types.user_profile_photos.UserProfilePhotos` object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned.
        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :return: instance of method :class:`aiogram.methods.get_user_profile_photos.GetUserProfilePhotos`
        """
        # DO NOT EDIT MANUALLY!!!
        # This method was auto-generated via `butcher`

        from aiogram.methods import GetUserProfilePhotos

        return GetUserProfilePhotos(
            user_id=self.id,
            offset=offset,
            limit=limit,
            **kwargs,
        ).as_(self._bot)
