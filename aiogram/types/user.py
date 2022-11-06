from __future__ import annotations

from typing import Optional

from ..utils import markdown
from ..utils.link import create_tg_link
from .base import TelegramObject


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
