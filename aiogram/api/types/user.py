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
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
