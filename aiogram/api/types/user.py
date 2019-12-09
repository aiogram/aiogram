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

    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name
