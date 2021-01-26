from __future__ import annotations

from typing import Optional

from .base import TelegramObject


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
    """User's or bot's first name"""
    last_name: Optional[str] = None
    """*Optional*. User's or bot's last name"""
    username: Optional[str] = None
    """*Optional*. User's or bot's username"""
    language_code: Optional[str] = None
    """*Optional*. `IETF language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_ of the user's language"""
    can_join_groups: Optional[bool] = None
    """*Optional*. True, if the bot can be invited to groups. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    can_read_all_group_messages: Optional[bool] = None
    """*Optional*. True, if `privacy mode <https://core.telegram.org/bots#privacy-mode>`_ is disabled for the bot. Returned only in :class:`aiogram.methods.get_me.GetMe`."""
    supports_inline_queries: Optional[bool] = None
    """*Optional*. True, if the bot supports inline queries. Returned only in :class:`aiogram.methods.get_me.GetMe`."""

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
